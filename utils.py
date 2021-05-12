import os
import sys
import time
import subprocess
import traceback
from unicodedata import normalize
import plyer
import playsound


def resource_path(rel_path):
    """ Thanks to: detly < https://stackoverflow.com/questions/4416336/adding-a-program-icon-in-python-gtk/4416367 > """
    dir_of_py_file = os.path.dirname(__file__)
    rel_path_to_resource = os.path.join(dir_of_py_file, rel_path)
    abs_path_to_resource = os.path.abspath(rel_path_to_resource)
    if abs_path_to_resource[-1:] != os.path.sep:
        abs_path_to_resource += os.path.sep
    return abs_path_to_resource


def notify(message, sound, icon):
    if message is not None:
        plyer.notification.notify(
            title='Clock by alef',
            message=message,
            app_icon=resource_path(icon),
            timeout=5,
        )

    if sound is not None:
        playsound.playsound(sound)


def load_font(archOS, fontpath, private=True, enumerable=False):
    '''
    Makes fonts located in file `fontpath` available to the font system.
    `private`     if True, other processes cannot see this font, and this
                  font will be unloaded when the process dies
    `enumerable`  if True, this font will appear when enumerating fonts
    See https://msdn.microsoft.com/en-us/library/dd183327(VS.85).aspx
    '''
    # This function was taken from
    # https://github.com/ifwe/digsby/blob/f5fe00244744aa131e07f09348d10563f3d8fa99/digsby/src/gui/native/win/winfonts.py#L15

    if "Windows" in archOS:
        from ctypes import windll, byref, create_string_buffer

        FR_PRIVATE = 0x10
        FR_NOT_ENUM = 0x20

        pathbuf = create_string_buffer(fontpath.encode())
        AddFontResourceEx = windll.gdi32.AddFontResourceExA

        flags = (FR_PRIVATE if private else 0) | (FR_NOT_ENUM if not enumerable else 0)
        numFontsAdded = AddFontResourceEx(byref(pathbuf), flags, 0)
        return bool(numFontsAdded)
    else:
        from fontTools.ttLib import TTFont
        try:
            TTFont(resource_path(fontpath))
            return True
        except:
            return False


def win_run_as_admin(argv=None, debug=False, force_admin=True):
    # https://stackoverflow.com/questions/19672352/how-to-run-python-script-with-elevated-privilege-on-windows (Gary Lee)

    from ctypes import windll
    shell32 = windll.shell32

    if argv is None and shell32.IsUserAnAdmin():
        # Already running as admin
        return True

    if argv is None:
        argv = sys.argv
    if hasattr(sys, '_MEIPASS'):
        # Support pyinstaller wrapped program.
        arguments = argv[1:]
    else:
        arguments = argv
    argument_line = u' '.join(arguments)
    executable = sys.executable
    if debug:
        print('Command line: ', executable, argument_line)
    console_mode = 0
    if debug:
        console_mode = 1
    ret = shell32.ShellExecuteW(None, u"runas", executable, argument_line, None, console_mode)
    if int(ret) <= 32:
        # Not possible to gain admin privileges
        if not force_admin:
            argument_line = "not_admin " + argument_line
            shell32.ShellExecuteW(None, u"open", executable, argument_line, None, console_mode)
        return False

    # Gaining admin privileges in process
    return None


def subprocess_args(include_stdout=True):
    # https: // github.com / pyinstaller / pyinstaller / wiki / Recipe - subprocess (by twisted)
    # The following is true only on Windows.
    if hasattr(subprocess, 'STARTUPINFO'):
        # On Windows, subprocess calls will pop up a command window by default
        # when run from Pyinstaller with the ``--noconsole`` option. Avoid this
        # distraction.
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        # Windows doesn't search the path by default. Pass it an environment so
        # it will.
        env = os.environ
    else:
        si = None
        env = None

    # ``subprocess.check_output`` doesn't allow specifying ``stdout``::
    #
    #   Traceback (most recent call last):
    #     File "test_subprocess.py", line 58, in <module>
    #       **subprocess_args(stdout=None))
    #     File "C:\Python27\lib\subprocess.py", line 567, in check_output
    #       raise ValueError('stdout argument not allowed, it will be overridden.')
    #   ValueError: stdout argument not allowed, it will be overridden.
    #
    # So, add it only if it's needed.
    if include_stdout:
        ret = {'stdout': subprocess.PIPE}
    else:
        ret = {}

    # On Windows, running this from the binary produced by Pyinstaller
    # with the ``--noconsole`` option requires redirecting everything
    # (stdin, stdout, stderr) to avoid an OSError exception
    # "[Error 6] the handle is invalid."
    ret.update({'stdin': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'startupinfo': si,
                'env': env})
    return ret


def WrapText(text, font, width):
    # ColdrickSotK
    # https://github.com/ColdrickSotK/yamlui/blob/master/yamlui/util.py#L82-L143
    """Wrap text to fit inside a given width when rendered.
    :param text: The text to be wrapped.
    :param font: The font the text will be rendered in.
    :param width: The width to wrap to."""

    text_lines = text.replace('\t', '    ').split('\n')
    if width is None or width == 0:
        return text_lines

    wrapped_lines = []
    for line in text_lines:
        line = line.rstrip() + ' '
        if line == ' ':
            wrapped_lines.append(line)
            continue

        # Get the leftmost space ignoring leading whitespace
        start = len(line) - len(line.lstrip())
        start = line.index(' ', start)
        while start + 1 < len(line):
            # Get the next potential splitting point
            next = line.index(' ', start + 1)
            if font.size(line[:next])[0] <= width:
                start = next
            else:
                wrapped_lines.append(line[:start])
                line = line[start + 1:]
                start = line.index(' ')
        line = line[:-1]
        if line:
            wrapped_lines.append(line)

    return wrapped_lines


def to_float(s, dec=1):
    num = ''.join(n for n in str(s) if n.isdigit() or n == "." or n == "-")
    try:
        return round(float(num), dec)
    except Exception:
        return 0.0


def elimina_tilde(cadena):
    # Use only in python 2. Not required (and will not work) on python 3

    try:
        trans_tab = dict.fromkeys(map(ord, u'\u0301\u0308'), None)
        s = unicode(cadena, "utf-8")
        cadena = normalize('NFKC', normalize('NFKD', s).translate(trans_tab))
    except:
        print("Error removing accent from string", cadena)
        print(traceback.format_exc())

    return cadena




