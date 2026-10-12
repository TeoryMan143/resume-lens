"""Entry point: python main.py --resume path/to/resume.txt --profile FULL_STACK_DEVELOPER"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from resume_lens import main

if __name__ == "__main__":
    sys.exit(main())
