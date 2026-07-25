import conftest_paths  # noqa: F401  (puts backend/ on sys.path)
import unittest
from unittest import mock
import wsl


class TestWinToWsl(unittest.TestCase):
    def test_drive_path(self):
        self.assertEqual(wsl.win_to_wsl(r"D:\LlamaForge\x"), "/mnt/d/LlamaForge/x")

    def test_forward_slash_input(self):
        self.assertEqual(wsl.win_to_wsl("C:/Users/a/b"), "/mnt/c/Users/a/b")

    def test_already_posix(self):
        self.assertEqual(wsl.win_to_wsl("/home/me/x"), "/home/me/x")


class TestListDistros(unittest.TestCase):
    def test_parses_utf16_verbose_output(self):
        raw = "  NAME      STATE    VERSION\n* Ubuntu    Running  2\n  Debian    Stopped  2\n"
        with mock.patch.object(wsl, "_run_text", return_value=raw):
            distros = wsl.list_distros()
        self.assertEqual(distros, [
            {"name": "Ubuntu", "state": "Running", "version": "2", "default": True},
            {"name": "Debian", "state": "Stopped", "version": "2", "default": False},
        ])

    def test_no_wsl_returns_empty(self):
        with mock.patch.object(wsl, "_run_text", side_effect=FileNotFoundError()):
            self.assertEqual(wsl.list_distros(), [])


class TestRun(unittest.TestCase):
    def _argv(self, sr):
        return sr.call_args[0][0]

    def test_run_builds_bash_lc_invocation(self):
        with mock.patch("subprocess.run") as sr:
            sr.return_value = mock.Mock(returncode=0, stdout="hi\n", stderr="")
            code, out, err = wsl.run("echo hi", distro="Ubuntu")
        args = self._argv(sr)
        self.assertEqual(args[:5], ["wsl.exe", "-d", "Ubuntu", "--", "bash"])
        self.assertEqual(args[5:], ["-lc", "echo hi", "bash"])
        self.assertEqual((code, out.strip()), (0, "hi"))

    def test_args_are_bound_as_positional_parameters(self):
        """`bash -lc SCRIPT NAME ARG` sets $0=NAME, $1=ARG - so the value is
        data the script dereferences, never text bash parses."""
        with mock.patch("subprocess.run") as sr:
            sr.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            wsl.run('rm -rf "$1"', "x; rm -rf ~", distro="Ubuntu")
        args = self._argv(sr)
        self.assertEqual(args[-3:], ['rm -rf "$1"', "bash", "x; rm -rf ~"])

    def test_popen_uses_the_same_binding(self):
        with mock.patch("subprocess.Popen") as sp:
            wsl.popen('echo "$1"', "a b; c", stdout=None, stderr=None, distro="Ubuntu")
        args = sp.call_args[0][0]
        self.assertEqual(args[-3:], ['echo "$1"', "bash", "a b; c"])

    def test_non_string_args_are_stringified(self):
        with mock.patch("subprocess.run") as sr:
            sr.return_value = mock.Mock(returncode=0, stdout="", stderr="")
            wsl.run('echo "$1"', 8081, distro="Ubuntu")
        self.assertEqual(self._argv(sr)[-1], "8081")


class TestShPath(unittest.TestCase):
    def test_tilde_becomes_home_so_it_expands_when_quoted(self):
        self.assertEqual(wsl.sh_path("~/.llamaforge/venv"),
                         '"$HOME"/.llamaforge/venv')

    def test_bare_tilde(self):
        self.assertEqual(wsl.sh_path("~"), '"$HOME"')

    def test_absolute_path_is_quoted(self):
        self.assertEqual(wsl.sh_path("/home/u/venv"), "/home/u/venv")

    def test_path_with_spaces_or_metacharacters_is_quoted(self):
        for p in ("/home/my venv", "/tmp/x;rm -rf ~", "/a$(id)b"):
            quoted = wsl.sh_path(p)
            self.assertTrue(quoted.startswith("'") and quoted.endswith("'"), quoted)


if __name__ == "__main__":
    unittest.main()
