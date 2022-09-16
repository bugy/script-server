# A issue running on OpenBSD and maybe other UNIX systems
Script-server terminates a script executor process by manipulating its process group. You will get a permission
denied error when running with a non-root user on OpenBDF. And maybe some other UNIX systems behivior like so, too.

Here's a tempoary workaround: Terminating the script process with finding and killing its subprocess.

You can apply this patch to `src/execution/process_base.py`:
```patch
--- process_base.py.old   Fri Sep 16 16:12:59 2022
+++ process_base.py.new     Fri Sep 16 14:20:14 2022
@@ -4,6 +4,7 @@
 import signal
 import subprocess
 import threading
+import psutil

 from react.observable import ReplayObservable
 from utils import os_utils
@@ -71,29 +72,37 @@
     def stop(self):
         if not self.is_finished():
             if not os_utils.is_win():
-                group_id = os.getpgid(self.get_process_id())
-                os.killpg(group_id, signal.SIGTERM)
+                psutil_self_proc = psutil.Process(self.get_process_id())
+                # Send SIGTERM to child processes.
+                for curr_sub_proc in psutil_self_proc.children(recursive=True):
+                    try:
+                        curr_sub_proc.terminate()
+                    except psutil.NoSuchProcess:
+                        pass

-                class KillChildren(object):
-                    def finished(self):
-                        try:
-                            os.killpg(group_id, signal.SIGKILL)
-                        except ProcessLookupError:
-                            # probably there are no children left
-                            pass
+                # Send SIGTERM to self.
+                psutil_self_proc.terminate()

-                self.add_finish_listener(KillChildren())
-
             else:
                 self.process.terminate()

             self._write_script_output('\n>> STOPPED BY USER\n')

+
     def kill(self):
         if not self.is_finished():
             if not os_utils.is_win():
-                group_id = os.getpgid(self.get_process_id())
-                os.killpg(group_id, signal.SIGKILL)
+                psutil_self_proc = psutil.Process(self.get_process_id())
+                # Send SIGKILL to child processes.
+                for curr_sub_proc in psutil_self_proc.children(recursive=True):
+                    try:
+                        curr_sub_proc.kill()
+                    except psutil.NoSuchProcess:
+                        pass
+
+                # Send SIGKILL to self.
+                psutil_self_proc.kill()
+
                 self._write_script_output('\n>> KILLED\n')
             else:
                 subprocess.Popen("taskkill /F /T /PID " + self.get_process_id())

```
This is a tempoary workaround and should not merge into master cause this is not portable and the "right" way,
and we do not know that running Script-server on what operating systems will cause that issue.
