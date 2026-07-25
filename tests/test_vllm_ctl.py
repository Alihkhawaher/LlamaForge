import conftest_paths  # noqa: F401
import unittest
from unittest import mock
import vllm_ctl


class TestFlagBuilding(unittest.TestCase):
    def test_settings_to_flags(self):
        flags = vllm_ctl.settings_to_flags({
            "tensor-parallel-size": "2",
            "gpu-memory-utilization": "0.9",
            "enforce-eager": "true",
            "disable-log-stats": "false",
        })
        self.assertEqual(flags[flags.index("--tensor-parallel-size") + 1], "2")
        self.assertEqual(flags[flags.index("--gpu-memory-utilization") + 1], "0.9")
        self.assertIn("--enforce-eager", flags)
        self.assertNotIn("--disable-log-stats", flags)   # false -> omitted

    def test_values_stay_one_argv_slot(self):
        """A knob value must never be split into extra arguments."""
        flags = vllm_ctl.settings_to_flags({"served-model-name": "a b --evil"})
        self.assertEqual(flags, ["--served-model-name", "a b --evil"])

    def test_junk_knob_names_are_dropped(self):
        flags = vllm_ctl.settings_to_flags({
            "ok-knob": "1", "bad; rm -rf ~": "1", "": "1", "--sneaky": "1"})
        self.assertEqual(flags, ["--ok-knob", "1"])

    def test_serve_script_binds_model_ref_as_a_parameter(self):
        script = vllm_ctl.build_serve_script("/home/u/.llamaforge/vllm-venv")
        self.assertIn("/home/u/.llamaforge/vllm-venv/bin/vllm serve", script)
        self.assertIn('"$1"', script)        # model ref is data, not syntax
        self.assertIn('--port "$2"', script)
        self.assertIn("--host 0.0.0.0", script)
        self.assertIn('"${@:3}"', script)    # flags forwarded verbatim

    def test_serve_script_expands_a_tilde_venv(self):
        script = vllm_ctl.build_serve_script("~/.llamaforge/vllm-venv")
        self.assertIn('"$HOME"/.llamaforge/vllm-venv/bin/vllm', script)


class TestManagerLifecycle(unittest.TestCase):
    def setUp(self):
        self.mgr = vllm_ctl.Manager(distro="Ubuntu", port=8081,
                                     venv="/home/u/.llamaforge/vllm-venv",
                                     logdir="/tmp/lf-logs")
        # start() spawns _await_ready, which polls /health every 3s for up to
        # READY_TIMEOUT (600s). Left alone those daemon threads outlive the test
        # and keep hammering a dead port for the rest of the run.
        patcher = mock.patch.object(vllm_ctl.Manager, "_await_ready")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_single_instance_guard(self):
        self.mgr.instances = [{"model_id": "a", "port": 8081, "state": "ready",
                               "started_at": 0}]
        ok, err = self.mgr.start("b", model_ref="b", flags=[])
        self.assertFalse(ok)
        self.assertIn("already", err.lower())

    def test_start_spawns_via_wsl_and_records_instance(self):
        with mock.patch("wsl.popen") as popen, \
             mock.patch("os.makedirs"), \
             mock.patch("builtins.open", mock.mock_open()):
            popen.return_value = mock.Mock()
            ok, err = self.mgr.start("Qwen/Qwen3-8B", model_ref="Qwen/Qwen3-8B",
                                     flags=["--tensor-parallel-size", "2"])
        self.assertTrue(ok, err)
        self.assertEqual(len(self.mgr.instances), 1)
        self.assertEqual(self.mgr.instances[0]["model_id"], "Qwen/Qwen3-8B")
        self.assertEqual(self.mgr.instances[0]["state"], "starting")
        # script first, then model ref / port / flags as positional parameters
        args = popen.call_args[0]
        self.assertIn("vllm serve", args[0])
        self.assertEqual(args[1], "Qwen/Qwen3-8B")
        self.assertEqual(list(args[3:]), ["--tensor-parallel-size", "2"])

    def test_malicious_model_ref_is_passed_as_data_not_shell(self):
        with mock.patch("wsl.popen") as popen, \
             mock.patch("os.makedirs"), \
             mock.patch("builtins.open", mock.mock_open()):
            popen.return_value = mock.Mock()
            self.mgr.start("evil", model_ref="x; rm -rf ~", flags=[])
        args = popen.call_args[0]
        self.assertNotIn("rm -rf", args[0])       # never reaches the script text
        self.assertEqual(args[1], "x; rm -rf ~")  # stays one opaque argument

    def test_stop_pkills_and_clears_instance(self):
        self.mgr.instances = [{"model_id": "a", "port": 8081, "state": "ready",
                               "started_at": 0}]
        with mock.patch("wsl.run", return_value=(0, "", "")) as run:
            self.mgr.stop("a")
        self.assertIn("pkill", run.call_args[0][0])
        self.assertEqual(self.mgr.instances, [])

    def test_status_reports_instances(self):
        self.mgr.instances = [{"model_id": "a", "port": 8081, "state": "ready",
                               "started_at": 123}]
        st = self.mgr.status()
        self.assertEqual(st[0]["model_id"], "a")
        self.assertEqual(st[0]["endpoint"], "http://127.0.0.1:8081")

    def test_reconcile_marks_offline_when_no_vllm_process(self):
        self.mgr.instances = [{"model_id": "a", "port": 8081, "state": "ready",
                               "started_at": 0}]
        with mock.patch("wsl.run", return_value=(1, "", "")):   # pgrep: nothing
            self.mgr.reconcile()
        self.assertEqual(self.mgr.instances, [])


if __name__ == "__main__":
    unittest.main()
