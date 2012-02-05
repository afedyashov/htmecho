#!/usr/bin/env python3

# On Windows OS piping might not work as expected for an app started by file association.
# For example: 
#   echo 123 | www.py
# Workarounds:
# * either call python explicitly: echo 123 | python www.py
# * or use a registry patch, ref: http://support.microsoft.com/default.aspx?kbid=321788

import sys
import os
import re
import platform
import subprocess
import tempfile
import codecs

def text_to_html(s):
	s = s.replace("&", "&amp;") # note: order maters
	s = s.replace("<", "&lt;")
	s = s.replace(">", "&gt;")
	s = s.replace('"', "&quot;")
	s = s.replace(' ', "&nbsp;")
	s = s.replace('\t', "&nbsp;&nbsp;&nbsp;&nbsp;")
	return s

def handle_input(i_f, o_f):
	total_lines_generated = 0
	total_lines_fetched = 0
	total_chars_fetched = 0
	template = get_html_template()
	for tmpl_line in template.split("\n"):
		if -1 == tmpl_line.find("<!-- OUTPUT -->"):
			o_f.write(tmpl_line + "\n")
			total_lines_generated += 1
		else:
			for line in i_f.readlines():
				total_lines_fetched += 1
				total_chars_fetched += len(line)
				line = line.rstrip()
				if len(line) == 0:
					line = " "
				htmline = "<div>" + text_to_html(line) + "</div>"
				o_f.write(htmline + "\n")	
				total_lines_generated += 1
	return { "total_lines_fetched": total_lines_fetched, "total_lines_generated": total_lines_generated, "total_chars_fetched": total_chars_fetched}

def get_html_template():
	return """
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Dummy</title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <style type="text/css">
    .sys 
    {
        font-size: small;	
        font-family: arial;
    }

    div 
    { 
        font-size: normal;
        font-family: monospace;
        white-space: nowrap;
    }
    </style>
	<script type="text/javascript" charset="utf-8">
		function enum_elements(predicate, action) {
			var ps = document.getElementsByTagName("div");
			for (var i = 0; i < ps.length; i++) {
				var str = ps[i].textContent;
				action(ps[i], predicate(str));
			}
		}
		
		function get_template()
		{
			return document.getElementById("grep_template").value;
		}

		function get_inverse()
		{
			return document.getElementById("grep_inverse").checked;
		}
		
		function grep_predicate(s)
		{
			template = get_template();
			inverse = get_inverse();
			result = true;
			if (template.length > 0)
			{
				var re = new RegExp(template);
				result = re.test(s);
			}
			return inverse ? !result : result;
		}
		
		function grep_action(e, state) {
			if (!state) {
				e.style.display = 'none'
			} else {
				e.style.display = 'block'
			}
		}
		
		function mark_action(e, state) {
			if (state) {
				e.style.background = document.getElementById("mark_color").value
			} else {
			}
		}

		function update_color() {			
			o = document.getElementById("mark_color")
			o.style.background = o.value
		}

		function grep() {
			enum_elements(grep_predicate, grep_action);
		}
		
		function mark() {
			enum_elements(grep_predicate, mark_action);
		}

		function auto_action() {
			if (document.getElementById("action_grep").checked)
				grep();
			else if (document.getElementById("action_mark").checked)
				mark();			
		}

		var grep_timer;	
		function auto_grep(e) {
			clearTimeout(grep_timer);				
			is_online = document.getElementById("online_grep").checked;
			if (is_online) { 
				grep_timer = setTimeout( grep, 200 );
			} else if (e && e.keyCode == 13) {
				grep();				
			}
		}

		var color_timer;
		function auto_color(e) {
			clearTimeout(color_timer);
			if (e && e.keyCode == 13) {
				update_color();				
			}
			else {
				color_timer = setTimeout( update_color, 200 );
			};
		}

    </script>

</head>

<body>

		<table class="sys">
		<tr>
			<td>
				<input type="text" id="grep_template" onkeyup="auto_grep(event)" />
				<input type="checkbox" name="online_grep" id="online_grep" checked="checked" />incremental
				<input type="checkbox" name="grep_inverse" id="grep_inverse" />inverse
				<input type="button" value="apply color" onclick="mark()" />
				<input type="text" id="mark_color" value="" onkeyup="auto_color(event)" />
			</td>
		</tr>
		</table>
	<!-- OUTPUT -->
</body>

</html>
	"""

def shell_open_file(filename):
	if platform.system() == "Windows":
		os.startfile(filename)
		return True
	elif platform.system() == "Linux":
		prc = subprocess.Popen(['xdg-open', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		prc.wait()
		return True
	return False

def get_flag(flag, args=sys.argv):
	try:
		args.index(flag)
		return True
	except:
		return False

def get_option(option, args=sys.argv):
	try:
		idx = args.index(option)
		return args[idx + 1]
	except:	
		return None

def get_help_msg():
	return """
  --help           prints this help message
  --input value    explicitly specifies an input file (othwerwise input is read from STDIN)
  --encoding value defines encoding to be used with an input file (valid only with --input), e.g. utf_8, utf_16_le, cp1251
  --test           (for testing purposes) performs all the work without actually opening the browser
  --stat           (for testing purposes) outputs number of lines fetched & generated while handling the input
	"""

def htmlize(args=sys.argv):
	if get_flag("--help", args=args):
		print (get_help_msg())
		exit(0)
	stdout_data = []
	testmode = get_flag("--test", args=args)
	verbose = testmode or get_flag("--verbose", args=args)
	statmode = get_flag("--stat", args=args)
	encoding = get_option("--encoding", args=args)
	input_filename = get_option("--input", args=args)
	if None != input_filename:
		assert os.path.isfile(input_filename), "--input keyword should be followed with an existing file name"
		in_file = codecs.open(input_filename, "r", encoding=encoding)
	else:
		in_file = sys.stdin
	(o_fd, o_filename) = tempfile.mkstemp('-www.html')
	o_fp = os.fdopen(o_fd, "w")
	stats = handle_input(in_file, o_fp)
	o_fp.close()
	if not testmode:
		shell_open_file(o_filename)
	if statmode:
		for (k, v) in stats.items():
			stdout_data.append("%s: %s" % (k, v))
	if verbose:
		stdout_data.append("output: %s" % (o_filename))
	return stdout_data

def selftest(testdir):
	root = os.path.abspath(testdir)
	for item in sorted(os.listdir(root)):
		fullname = os.path.join(root, item)
		if not os.path.isfile(fullname):
			continue
		m = re.search(r'\-enc\-([\w\d\_\-]+)\.', item)
		if m:
			encoding = m.group(1)
			args = [
				"--input", fullname,
				"--encoding", encoding,
				"--test",
				"--stat"
				]
			print ("invoking:", " ".join(args))
			try:
				res = htmlize(args=args)
			except Exception as e:
				res = [ "Exception: %s" % (str(e)) ]
			for s in res: print (s)
if __name__=="__main__":
	sanitydir = get_option("--sanitydir")
	if sanitydir and os.path.isdir(sanitydir):
		selftest(sanitydir)
	else:
		res = htmlize(sys.argv)
		for s in res: print (s)
	exit()	
