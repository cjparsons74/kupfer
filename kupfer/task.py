import threading

from kupfer import scheduler, pretty

class Task (object):
	"""Represent a task that can be done in the background"""
	def __init__(self, name):
		self.name = name

	def __str__(self):
		return self.name

	def is_thread(self):
		return False

	def run(self):
		raise NotImplementedError

class StepTask (Task):
	"""A step task runs a part of the task in StepTask.step,
	doing final cleanup in StepTask.finish, which is guaranteed to
	be called regardless of exit or failure mode
	"""
	def step(self):
		pass
	def finish(self):
		pass
	def run(self):
		try:
			while True:
				if not self.step():
					break
				yield
		finally:
			self.finish()

class ThreadTask (Task, threading.Thread):
	"""Run in a thread"""
	def __init__(self, name):
		Task.__init__(self, name)
		threading.Thread.__init__(self)
		self.__thread_done = False
		self.__thread_started = False

	def is_thread(self):
		return True

	def thread_do(self):
		"""Override this to run what should be done in the thread"""
		raise NotImplementedError

	def __thread_run(self):
		try:
			self.__retval = self.thread_do()
		finally:
			self.__thread_done = True

	def run(self):
		while True:
			if not self.__thread_started:
				# swizzle the methods for Thread
				self.run = self.__thread_run
				self.start()
				self.__thread_started = True
			elif self.__thread_done:
				return
			yield

class TaskRunner (pretty.OutputMixin):
	"""Run Tasks in the idle Loop"""
	def __init__(self, end_on_finish):
		self.task_iters = {}
		self.thread_iters = {}
		self.idle_timer = scheduler.Timer(True)
		self.end_on_finish = end_on_finish
		scheduler.GetScheduler().connect("finish", self._finish_cleanup)

	def add_task(self, task):
		"""Register @task to be run"""
		if task.is_thread():
			# start thread
			self.thread_iters[task] = task.run()
			# run through all threads
			self._step_tasks(self.thread_iters)
		else:
			self.task_iters[task] = task.run()
		self._setup_timers()

	def _setup_timers(self):
		if self.task_iters:
			self.idle_timer.set_idle(self._step_tasks, self.task_iters)

	def _step_tasks(self, tasks):
		for task, task_iter in tasks.items():
			try:
				task_iter.next()
			except StopIteration:
				self.output_debug("Task done:", task)
				del tasks[task]
		self._setup_timers()

	def _finish_cleanup(self, sched):
		if self.end_on_finish:
			self.task_iters.clear()
			self.thread_iters.clear()
			return
		self._step_tasks(self.thread_iters)
		if self.task_iters or self.thread_iters:
			self.output_info("Uncompleted tasks:")
			for task in self.task_iters:
				self.output_info(task)
			for task in self.thread_iters:
				self.output_info(task)
