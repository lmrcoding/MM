import subprocess
import json

def scan_packages():
    try:
        output = subprocess.check_output(["pip", "list", "--format", "json"])
        packages = json.loads(output)

        results = []
        for pkg in packages:
            results.append({
                "name": pkg["name"],
                "version": pkg["version"]
                # In future: hook into CVE feeds or safety DBs
            })

        return results

    except Exception as e:
        return {"error": str(e)}
