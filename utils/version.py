"""Version management."""
import subprocess


def get_version():
    """Get version from git tags, fallback to version.py or 'dev'."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True,
            timeout=1
        )
        if result.returncode == 0:
            return result.stdout.strip().lstrip('v')
    except:
        pass
    
    # Fallback to version.py
    try:
        from version import __version__
        return __version__
    except:
        pass
    
    return "1.0.0"
