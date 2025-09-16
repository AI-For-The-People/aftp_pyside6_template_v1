from .main import main
from app.core.crash_guard import install as _aftp_install_crash_guard
_aftp_install_crash_guard()  # install crash/qt logging early

if __name__ == '__main__':
    main()
