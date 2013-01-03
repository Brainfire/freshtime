import pygtk
pygtk.require('2.0')
import gtk
import datetime
from refreshbooks import api

class TimeEntryScreen:
    def __init__(self, freshbooks):
        self.freshbooks = freshbooks
        self.entry_screen = gtk.VBox(False, 0)

    def refresh_time_list(self, widget):
        print "refreshing"

    def start_time(self, widget):
        self.start_button.hide()
        self.stop_button.show()
        print "start timer"

    def stop_time(self, widget):
        self.stop_button.hide()
        self.start_button.show()
        print "stop timer"

    def build_time_entry(self):
        time_entry_box = gtk.HBox(False, 0)

        project_chooser = gtk.ComboBox()
        project_chooser.show()
        time_entry_box.pack_start(project_chooser, True, True, 0)

        description_entry = gtk.Entry()
        description_entry.show()
        time_entry_box.pack_start(description_entry, True, True, 0)

        self.start_button = create_button("Start", self.start_time)
        time_entry_box.pack_start(self.start_button, True, True, 0)

        self.stop_button = create_button("Stop", self.stop_time, show=False)
        time_entry_box.pack_start(self.stop_button, True, True, 0)

        return time_entry_box

    def build_time_list(self):
        time_list_box = gtk.VBox(False, 0)

        # Create a new scrolled window, with scrollbars only if needed
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        model = gtk.ListStore(int, str, str, str, bool)
        tree_view = gtk.TreeView(model)
        scrolled_window.add_with_viewport (tree_view)
        tree_view.show()

        freshbook_times = self.freshbooks.time_entry.list()
        for time_entry in freshbook_times.time_entries.time_entry:
            project_name = int(time_entry.project_id)
            notes = str(time_entry.notes)

            hour = int(time_entry.hours.pyval)
            minute = ((time_entry.hours.pyval - hour) * 60)
            hours = datetime.time(hour=hour, minute=minute).strftime("%I:%M")

            time_date = str(time_entry.date)
            billed = bool(time_entry.billed)

            model.append([project_name, notes, hours, time_date, billed])

        project_cell = gtk.CellRendererText()
        project_column = gtk.TreeViewColumn("Project", project_cell, text=0)
        tree_view.append_column(project_column)

        notes_cell = gtk.CellRendererText()
        notes_column = gtk.TreeViewColumn("Notes", notes_cell, text=1)
        tree_view.append_column(notes_column)

        hours_cell = gtk.CellRendererText()
        hours_column = gtk.TreeViewColumn("Hours", hours_cell, text=2)
        tree_view.append_column(hours_column)

        date_cell = gtk.CellRendererText()
        date_column = gtk.TreeViewColumn("Date", date_cell, text=3)
        tree_view.append_column(date_column)

        billed_cell = gtk.CellRendererText()
        billed_column = gtk.TreeViewColumn("Billed", billed_cell, text=4)
        tree_view.append_column(billed_column)

        scrolled_window.show()
        time_list_box.pack_start(scrolled_window, True, True, 0)

        refresh_button = create_button("Refresh", self.refresh_time_list, stock=gtk.STOCK_REFRESH)
        time_list_box.pack_start(refresh_button, True, True, 0)

        return time_list_box

    def build_screen(self):
        time_entry_box = self.build_time_entry()
        time_entry_box.show()
        self.entry_screen.pack_start(time_entry_box, True, True, 0)

        time_list_box = self.build_time_list()
        time_list_box.show()
        self.entry_screen.pack_start(time_list_box, True, True, 0)

    def render(self):
        self.build_screen()

        return self.entry_screen

class Freshtime:
    def __init__(self):
        #Setup Freshbooks API
        self.freshbooks = api.TokenClient('brainfirellc.freshbooks.com', '19ed4c37fdecbbd3d537603afdc9c0b2', user_agent='Freshtime/1.0')

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Freshtime")
        self.window.set_border_width(10)
        self.window.set_size_request(200, 200)

        # Close app on title bar close
        self.window.connect("destroy", lambda wid: gtk.main_quit())
        self.window.connect("delete_event", lambda a1,a2:gtk.main_quit())

        # Create boxes
        time_entry_screen = TimeEntryScreen(self.freshbooks)
        self.entry_screen = time_entry_screen.render() 


        self.window.add(self.entry_screen)

        # Window Display
        self.entry_screen.show()
        self.window.show()

    def main(self):
        gtk.main()

def create_button(label, callback, stock=None, show=True):
    button = gtk.Button(label=label, stock=stock)
    button.connect("clicked", callback)

    if show:
        button.show()

    return button

print __name__
if __name__ == "__main__":
    freshtime = Freshtime()
    freshtime.main()
