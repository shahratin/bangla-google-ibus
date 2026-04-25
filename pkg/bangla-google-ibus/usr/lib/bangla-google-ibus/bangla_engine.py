import urllib.request
import urllib.parse
import json
import threading
import gi
gi.require_version('IBus', '1.0')
from gi.repository import IBus, GLib, GObject

def get_bangla_suggestions(text: str, num: int = 8) -> list[str]:
    url = "https://inputtools.google.com/request"
    params = urllib.parse.urlencode({
        "text": text,
        "itc": "bn-t-i0-und",
        "num": num,
        "cp": 0, "cs": 1,
        "ie": "utf-8", "oe": "utf-8"
    })
    try:
        with urllib.request.urlopen(f"{url}?{params}", timeout=3) as r:
            data = json.loads(r.read().decode("utf-8"))
            if data[0] == "SUCCESS":
                return data[1][0][1]
            return []
    except Exception:
        return []


class BanglaEngine(IBus.Engine):
    __gtype_name__ = "BanglaEngine"

    def __init__(self):
        super().__init__()
        self._buffer = ""          # accumulates what user types in roman
        self._lookup_table = IBus.LookupTable.new(9, 0, True, True)
        self._suggestions = []

    def do_process_key_event(self, keyval, keycode, state):
        # Ignore key release events
        if state & IBus.ModifierType.RELEASE_MASK:
            return False

        # char = chr(keyval)
        char = chr(keyval) if keyval < 0x110000 else "" 

        # Backspace — remove last char from buffer
        if keyval == IBus.KEY_BackSpace:
            if self._buffer:
                self._buffer = self._buffer[:-1]
                if self._buffer:
                    self._fetch_and_show(self._buffer)
                else:
                    self._clear()
                return True
            return False

        # Space — commit the top suggestion (or the buffer as-is)
        if keyval == IBus.KEY_space:
            if self._suggestions:
                self._commit(self._suggestions[0])
            elif self._buffer:
                self.commit_text(IBus.Text.new_from_string(self._buffer))
                self._clear()
            else:
                return False  # let space pass through normally
            return True

        if keyval == IBus.KEY_Return:
            if self._suggestions:
                self._commit(self._suggestions[0])
            elif self._buffer:
                self.commit_text(IBus.Text.new_from_string(self._buffer))
                self._clear()
            else:
                return False  # let space pass through normally
            return True

        # Number keys 1-9 — pick suggestion by number
        if IBus.KEY_1 <= keyval <= IBus.KEY_9 and self._suggestions:
            index = keyval - IBus.KEY_1
            if index < len(self._suggestions):
                self._commit(self._suggestions[index])
            return True

        # Escape — cancel and clear
        if keyval == IBus.KEY_Escape:
            if self._buffer:
                self._clear()
                return True
            return False

        # Regular letter — add to buffer
        if char.isalpha():
            self._buffer += char
            self.update_preedit_text(
                IBus.Text.new_from_string(self._buffer), len(self._buffer), True
            )
            self._fetch_and_show(self._buffer)
            return True

        return False

    def _fetch_and_show(self, text):
        # Fetch in a background thread so typing stays responsive
        def fetch():
            suggestions = get_bangla_suggestions(text)
            GLib.idle_add(self._update_lookup_table, suggestions)
        threading.Thread(target=fetch, daemon=True).start()

    def _update_lookup_table(self, suggestions):
        self._suggestions = suggestions
        self._lookup_table.clear()
        for word in suggestions:
            self._lookup_table.append_candidate(IBus.Text.new_from_string(word))
        self.update_lookup_table(self._lookup_table, True)

    def _commit(self, word):
        self.commit_text(IBus.Text.new_from_string(word + " "))
        self._clear()

    def _clear(self):
        self._buffer = ""
        self._suggestions = []
        self._lookup_table.clear()
        self.update_preedit_text(IBus.Text.new_from_string(""), 0, False)
        self.hide_lookup_table()

    def do_focus_out(self):
        self._clear()

    def do_reset(self):
        self._clear()


def main():
    IBus.init()
    bus = IBus.Bus()

    if not bus.is_connected():
        print("ERROR: IBus daemon is not running. Start it with: ibus-daemon -drx")
        return

    factory = IBus.Factory.new(bus.get_connection())
    factory.add_engine("bangla-google", GObject.type_from_name("BanglaEngine"))

    bus.request_name("org.freedesktop.IBus.BanglaGoogle", 0)
    IBus.main()

if __name__ == "__main__":
    main()
