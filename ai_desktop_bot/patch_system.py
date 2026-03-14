import subprocess

def apply_patch(file_path, fix):
    try:
        if isinstance(fix, dict) and fix.get("type") == "pip_install":
            pkg = fix["package"]
            print(f"Installing dependency: {pkg}")
            subprocess.run(["pip", "install", pkg])
            return True

        # fallback (code patch)
        with open(file_path, "w") as f:
            f.write(fix)

        return True

    except Exception as e:
        print("Patch error:", e)
        return False