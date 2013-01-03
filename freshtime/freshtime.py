import pygtk
pygtk.require('2.0')
import gtk
import datetime
from refreshbooks import api

class FreshbooksTimeBackend():
    def __init__(self, options):
        self.connection = api.TokenClient(
            options['domain'],
            options['token'],
            user_agent=options['user_agent'])
        self.project_list = None
        self.task_list = None 
        self.entry_list = None

    @property
    def tasks(self):
        if self.task_list == None:
            self.task_list = self.populate_tasks()

        return self.task_list

    @property
    def projects(self):
        if self.project_list == None:
            self.project_list = self.populate_projects(self.tasks)

        return self.project_list

    @property
    def entries(self):
        if self.entry_list == None:
            self.entry_list = self.populate_entries()

        return self.entry_list

    def refresh_entries(self):
        self.entry_list = None;

    def populate_entries(self):
        entries_response = self.connection.time_entry.list()
        entries = {}

        for entry in entries_response.time_entries.time_entry:
            entry_item = {
                'id': str(entry.time_entry_id),
                'project': self.projects[str(entry.project_id)],
                'task': self.tasks[str(entry.task_id)],
                'notes': str(entry.notes),
                'hours': entry.hours.pyval,
                'date': datetime.datetime.strptime(str(entry.date), "%Y-%M-%d"),
                'billed': bool(entry.billed)
            }

            entries[entry_item['id']] = entry_item

        return entries 

    def populate_tasks(self):
        task_response = self.connection.task.list()
        tasks = {}

        for task in task_response.tasks.task:
            task_item = {
                'id': str(task.task_id),
                'name': str(task.name),
                'description': str(task.description),
                'billable': bool(task.billable),
                'rate': float(task.rate.pyval)
            }

            tasks[task_item['id']] = task_item

        return tasks

    def populate_projects(self, tasks):
        project_response = self.connection.project.list()
        projects = {}

        #Process tasks
        for project in project_response.projects.project:
            project_item = {
                'id': str(project.project_id),
                'name': str(project.name),
                'description': str(project.description),
                'tasks': {}
            }

            for task in project.tasks.task:
                task_id = str(task.task_id)
                project_item['tasks'][task_id] = tasks[task_id] 

            projects[project_item['id']] = project_item

        return projects

class TimeEntryScreen:
    def __init__(self, backend):
        self.backend = backend 
        self.entry_screen = gtk.VBox(False, 0)
        self.time_entry_box = gtk.HBox(False, 0)
        self.time_list_box = gtk.VBox(False, 0)

        self.time_start = None;
        self.time_stop = None;
        self.round_to = 1;

    def refresh_time_list(self, widget):
        self.backend.refresh_entries()

    def start_time(self, widget):
        self.time_start = datetime.datetime.now()

        self.start_button.hide()
        self.stop_button.show()


    def stop_time(self, widget):
        tm = datetime.datetime.now()
        tm += datetime.timedelta(minutes=self.round_to)
        tm -= datetime.timedelta(minutes=tm.minute % self.round_to,
                         seconds=tm.second,
                         microseconds=tm.microsecond)
        self.time_stop = tm

        hours,minutes = self.calculate_time_logged()
        print "{}:{}".format(hours, minutes)

        self.stop_button.hide()
        self.start_button.show()

    def calculate_time_logged(self):
        delta = self.time_stop - self.time_start
        hours = delta.seconds/3600
        minutes = (delta.seconds/60) % 60

        if minutes == 0:
            minutes = self.round_to

        self.time_stop = None;
        self.time_start = None;

        return hours, minutes

    def build_time_entry(self):
        task_chooser = gtk.combo_box_new_text()
        projects = self.backend.projects

        for project_id, project in projects.iteritems():
            for task_id, task in project['tasks'].iteritems():
                task_chooser.append_text("{} - {}".format(project['name'], task['name']))
        

        task_chooser.show()
        self.time_entry_box.pack_start(task_chooser, True, True, 0)

        description_entry = gtk.Entry()
        description_entry.show()
        self.time_entry_box.pack_start(description_entry, True, True, 0)

        self.start_button = create_button("Start", self.start_time)
        self.time_entry_box.pack_start(self.start_button, True, True, 0)

        self.stop_button = create_button("Stop", self.stop_time, show=False)
        self.time_entry_box.pack_start(self.stop_button, True, True, 0)

    def build_time_list(self):
        # Create a new scrolled window, with scrollbars only if needed
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        model = gtk.ListStore(str, str, str, str, str, bool)
        tree_view = gtk.TreeView(model)
        scrolled_window.add_with_viewport (tree_view)
        tree_view.show()

        for entry_id, entry in self.backend.entries.iteritems():
            project_name = entry['project']['name']
            task_name = entry['task']['name']

            hour = int(entry['hours'])
            minute = ((entry['hours'] - hour) * 60)
            hours = datetime.time(hour=hour, minute=minute).strftime("%I:%M")

            time_date = entry['date'].strftime("%M/%d/%Y")

            model.append([project_name, task_name, entry['notes'], hours, time_date, entry['billed']])

        project_cell = gtk.CellRendererText()
        project_column = gtk.TreeViewColumn("Project", project_cell, text=0)
        tree_view.append_column(project_column)

        task_cell = gtk.CellRendererText()
        task_column = gtk.TreeViewColumn("Task", task_cell, text=1)
        tree_view.append_column(task_column)

        notes_cell = gtk.CellRendererText()
        notes_column = gtk.TreeViewColumn("Notes", notes_cell, text=2)
        tree_view.append_column(notes_column)

        hours_cell = gtk.CellRendererText()
        hours_column = gtk.TreeViewColumn("Hours", hours_cell, text=3)
        tree_view.append_column(hours_column)

        date_cell = gtk.CellRendererText()
        date_column = gtk.TreeViewColumn("Date", date_cell, text=4)
        tree_view.append_column(date_column)

        billed_cell = gtk.CellRendererText()
        billed_column = gtk.TreeViewColumn("Billed", billed_cell, text=5)
        tree_view.append_column(billed_column)

        scrolled_window.show()
        self.time_list_box.pack_start(scrolled_window, True, True, 0)

        refresh_button = create_button("Refresh", self.refresh_time_list, stock=gtk.STOCK_REFRESH)
        self.time_list_box.pack_start(refresh_button, True, True, 0)

    def build_screen(self):
        self.build_time_entry()
        self.time_entry_box.show()

        self.build_time_list()
        self.time_list_box.show()

    def render(self):
        self.build_screen()

        self.entry_screen.pack_start(self.time_entry_box, True, True, 0)
        self.entry_screen.pack_start(self.time_list_box, True, True, 0)
        return self.entry_screen

class Freshtime:
    def __init__(self):
        #Setup Freshbooks API
        
        options = {
            'domain': 'brainfirellc.freshbooks.com',
            'token': '19ed4c37fdecbbd3d537603afdc9c0b2',
            'user_agent': 'Freshtime/1.0'
        }

        self.backend = FreshbooksTimeBackend(options)

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Freshtime")
        self.window.set_border_width(10)
        self.window.set_size_request(400, 200)

        # Close app on title bar close
        self.window.connect("destroy", lambda wid: gtk.main_quit())
        self.window.connect("delete_event", lambda a1,a2:gtk.main_quit())

        # Create boxes
        time_entry_screen = TimeEntryScreen(self.backend)
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
