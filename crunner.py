#!/usr/bin/python3
import os, collections, subprocess, datetime, threading
import config

import gi
gi.require_version('Gtk','3.0')
gi.require_version('GtkSource','3.0')
from gi.repository import GLib, Gtk, GtkSource, GObject, Pango
GObject.type_register(GtkSource.View)

class CRunner:
	def __init__(self):
		self.output = ""
		self.current_file = None
		self.init_gtk()

	def init_gtk(self):
		# Load interface #
		basepath = os.path.dirname(os.path.realpath(__file__))
		builder = Gtk.Builder()
		builder.add_from_file(os.path.join(basepath,"crunner.glade"))
		builder.connect_signals(self)

		# GUI objects #
		self.window = builder.get_object("crunner")
		self.code_editor = builder.get_object("code_editor")
		self.output_panel = builder.get_object("output_panel")
		self.output_scroll = builder.get_object("output_scroll")
		self.language_selector = builder.get_object("language_selector")
		self.action_selector = builder.get_object("action_selector")
		self.run_icon = builder.get_object("more_button").get_related_action()

		# Text and data buffers #
		self.output_buffer = self.output_panel.get_buffer()
		self.code_buffer = self.code_editor.get_buffer()
		self.languages = builder.get_object("languages")
		self.actions = builder.get_object("actions")

		# Editor highlighting and configuration #
		self.lang_manager = GtkSource.LanguageManager()
		self.style_manager = GtkSource.StyleSchemeManager()
		self.code_buffer.set_style_scheme(self.style_manager.get_scheme(config.editor['style']))
		self.font = Pango.FontDescription(config.editor['font'])
		self.code_editor.modify_font(self.font)
		self.output_panel.modify_font(self.font)

		# Populate languages menu #
		self.languages.clear()
		slanguages = sdict(config.languages)
		for lang, desc in slanguages.items():	
			self.languages.append([lang])
		self.language_selector.set_active_id("python")

		# Final connections #
		self.window.connect("delete-event", Gtk.main_quit)
		
		# New document #
		self.new_action()
		
		# Show window #
		self.window.resize(512,480)
		self.window.show_all()
		builder.get_object("menubar1").hide()
		self.code_editor.grab_focus()

		self.set_running(False)

	def set_running(self,is_running):
		self.is_running = is_running
		if is_running:
			self.run_icon.set_stock_id("gtk-media-stop")
		else:
			self.run_icon.set_stock_id("gtk-execute")

	def language_changed(self,selector=None):
		lang = self.language_selector.get_active_id()
		if lang != None:
			actions = config.languages[lang]['actions']
			default = config.languages[lang]['action']
			if self.code_buffer:
				if 'syntax' in config.languages[lang]:
					syntax = config.languages[lang]['syntax']
					syntax_object = self.lang_manager.get_language(syntax)
					self.code_buffer.set_highlight_syntax(True)
					self.code_buffer.set_language(syntax_object)
				else:
					self.code_buffer.set_highlight_syntax(False)
			self.actions.clear()
			for action,y in sdict(actions).items():
				self.actions.append([action])
			self.action_selector.set_active_id(default)

	def run_action(self,button=None):
		if self.is_running:
			return

		lang = self.language_selector.get_active_id()
		act = self.action_selector.get_active_id()
		code = self.get_code()

		def append_output(out):
			if(out and (type(out) is str)):
				self.output += out
				self.output_buffer.set_text(self.output)

		def safe_append_output(out):
			GLib.idle_add(append_output, out)

		def run_thread():
			executor(code, lang, act, safe_append_output)
			GLib.idle_add(self.set_running, False)

		self.set_running(True)
		append_output("\n\n")

		thread = threading.Thread(target=run_thread)
		thread.daemon = True
		thread.start()

	def new_action(self,button=None):
		self.current_file = None
		self.code_buffer.set_text("")
		self.update_title()
	
	def open_action(self,button=None):
		chooser = Gtk.FileChooserDialog("Open", self.window, Gtk.FileChooserAction.OPEN, 
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
		if self.current_file:
			chooser.set_filename(self.current_file)
		response = chooser.run()
		if response == Gtk.ResponseType.OK:
			self.current_file = chooser.get_filename()
			loader = open(self.current_file, "r")
			self.code_buffer.set_text(loader.read())
			loader.close()
		chooser.destroy()
		self.update_title()

	def saveas_action(self,button=None):
		chooser = Gtk.FileChooserDialog("Save", self.window, Gtk.FileChooserAction.SAVE, 
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
		if self.current_file:
			chooser.set_filename(self.current_file)
		chooser.set_do_overwrite_confirmation(True)
		response = chooser.run()
		if response == Gtk.ResponseType.OK:
			self.current_file = chooser.get_filename()
			self.save_action()
		chooser.destroy()
		self.update_title()
	
	def save_action(self,button=None):
		if self.current_file:
			writer = open(self.current_file, "w")
			code = self.get_code()
			writer.write(code)
			writer.close()
		else:
			self.saveas_action()

	def clear_action(self,button=None):
		self.output = ""
		self.output_buffer.set_text(self.output)
	
	def get_code(self):
		return self.code_buffer.get_text(
			self.code_buffer.get_start_iter(),
			self.code_buffer.get_end_iter(),True
		)

	def output_changed(self,x=None,y=None):
		adj = self.output_scroll.get_vadjustment()
		adj.set_value(adj.get_upper() - adj.get_page_size())
	
	def update_title(self):
		if self.current_file:
			self.window.set_title("crunner - %s" % (self.current_file))
		else:
			self.window.set_title("crunner")

	def exit_action(self,x=None):
		Gtk.main_quit()

def sdict(dict):
	return collections.OrderedDict(sorted(dict.items()))

def clean(lang):
	try:
		file = lang['clean']
		if os.path.exists(file):
			os.remove(file)
	except:
		pass

def executor(code, language, action, append_output):
	lang = config.languages[language]
	if action == None:
		action = lang['action']
	act = lang['actions'][action]
	
	clean(lang)
	t_start = datetime.datetime.now()
	append_output("#[%s] %s\n" % (action,str(t_start)))
	for sub in act:
		try:
			p = subprocess.Popen(sub, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

			# Write standard input (if applicable) #
			if code and (type(code) is str):
				p.stdin.write(code)
			p.stdin.close()

			# Read and collect standard output (until EOF) #
			line = p.stdout.readline()
			while line:
				append_output(line)
				line = p.stdout.readline()
			p.stdout.close()

			# Ensure process has completed #
			while p.poll() == None:
				pass

			# Gather return code #
			if p.returncode != 0:
				append_output("#[ret] %d\n" % (p.returncode))

		except Exception as e:
			print(e)
			append_output("#[err] Critical error during execution\n")

		code = None

	t_end = datetime.datetime.now()
	clean(lang)

	delta = t_end - t_start
	append_output("#[end] (%.3fs)" % (delta.total_seconds()))

	return True

CRunner()
Gtk.main()
