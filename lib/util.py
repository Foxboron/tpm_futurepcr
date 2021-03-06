import hashlib
import signify.fingerprinter
import subprocess

NUM_PCRS = 24
PCR_SIZE = hashlib.sha1().digest_size

def to_hex(buf):
    import binascii
    return binascii.hexlify(buf).decode()

def hexdump(buf):
    for i in range(0, len(buf), 16):
        row = buf[i:i+16]
        offs = "0x%08x:" % i
        hexs = ["%02X" % b for b in row] + ["  "] * 16
        text = [chr(b) if 0x20 < b < 0x7f else "." for b in row] + [" "] * 16
        print(offs, " ".join(hexs[:16]), "|%s|" % "".join(text[:16]))

def hash_file(path, digest="sha1"):
    h = getattr(hashlib, digest)()
    with open(path, "rb") as fh:
        buf = True
        buf_size = 4 * 1024 * 1024
        while buf:
            buf = fh.read(buf_size)
            h.update(buf)
    return h.digest()

def hash_pecoff(path, digest="sha1"):
    with open(path, "rb") as fh:
        fpr = signify.fingerprinter.AuthenticodeFingerprinter(fh)
        fpr.add_authenticode_hashers(getattr(hashlib, digest))
        return fpr.hash()[digest]
    return None

def init_empty_pcrs():
    pcrs = {x: (b"\xFF" if x in {17, 18, 19, 20, 21, 22} else b"\x00") * PCR_SIZE
            for x in range(NUM_PCRS)}
    return pcrs

def read_current_pcr(idx):
    res = subprocess.run(["tpm2_pcrlist", "-L", "sha1:%d" % idx, "-Q", "-o", "/dev/stdout"],
                         stdout=subprocess.PIPE)
    res.check_returncode()
    return res.stdout

def find_mountpoint_by_partuuid(partuuid):
    res = subprocess.run(["findmnt", "-S", "PARTUUID=%s" % partuuid, "-o", "TARGET", "-r", "-n"],
                         stdout=subprocess.PIPE)
    res.check_returncode()
    return res.stdout.splitlines()[0].decode()
