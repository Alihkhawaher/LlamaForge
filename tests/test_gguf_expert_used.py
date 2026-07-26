import conftest_paths  # noqa: F401
import os, struct, tempfile, unittest
import gguf


def _s(text):
    b = text.encode("utf-8")
    return struct.pack("<Q", len(b)) + b


def _kv_str(key, val):
    return _s(key) + struct.pack("<I", 8) + _s(val)


def _kv_u32(key, val):
    return _s(key) + struct.pack("<I", 4) + struct.pack("<I", val)


def _write_gguf(path, kvs):
    with open(path, "wb") as f:
        f.write(b"GGUF")
        f.write(struct.pack("<I", 3))
        f.write(struct.pack("<Q", 0))
        f.write(struct.pack("<Q", len(kvs)))
        f.write(b"".join(kvs))


class TestExpertUsed(unittest.TestCase):
    def test_expert_used_count_surfaced(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "m.gguf")
        _write_gguf(p, [
            _kv_str("general.architecture", "llama"),
            _kv_u32("llama.block_count", 32),
            _kv_u32("llama.expert_count", 128),
            _kv_u32("llama.expert_used_count", 8),
        ])
        meta = gguf.metadata(p)
        self.assertEqual(meta["expert_count"], 128)
        self.assertEqual(meta["expert_used_count"], 8)


if __name__ == "__main__":
    unittest.main()
