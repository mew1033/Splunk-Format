import sublime
import sublime_plugin
import re


class SplunkFormatCommand(sublime_plugin.TextCommand):
	def formatSplunkSearch(self, search):
		origString = search

		workingString = origString[:]

		# Strip whitespace
		workingString = workingString.strip()

		# Replace Strings with placeholder
		# Regex from http://www.bbosearch.com/pretty
		stgs = re.findall(r'\"[^\"\\]*(?:\\.[^\"\\]*)*\"', workingString)
		workingString = re.sub(r'\"[^\"\\]*(?:\\.[^\"\\]*)*\"', 'STRINGSTRINGSTRINGYSTRING', workingString)

		def findSubsearches(inString):
			# Pull out subsearches
			capturing = False
			count = 0
			start = 0
			r = []
			for i, c in enumerate(inString):
				if c == ']':
					if not capturing:
						raise "Everything is broken! You can't start with a ]!"
					if count > 0:
						count -= 1
					else:
						end = i
						capturing = False
						r.append(inString[start:end + 1])
				if c == '[':
					if capturing:
						count += 1
					else:
						start = i
						count = 0
						capturing = True
			return r

		def formatSubSearches(subsearches, level=1):
			# [|inputlookup cis_mappings.csv | [ do a things] eval check_id = STRINGSTRINGSTRINGYSTRING + check_id | table check_id nova_profile]
			r = []
			for x in subsearches:
				moarSubSearchs = findSubsearches(x.strip("[]"))
				if moarSubSearchs:
					for y in moarSubSearchs:
						x = x.replace(y, 'SUBSEARCHFTW%s' % level)
					moarSubSearchs = formatSubSearches(moarSubSearchs, level=level + 1)
					for y in moarSubSearchs:
						x = x.replace("SUBSEARCHFTW%s" % level, y, 1)
				x = re.sub(r"^(\s+?)?\[", r"[\n" + " " * level * 4, x)
				x = re.sub(r"(?:\s+?)?\|", r"\n" + " " * level * 4 + "|", x)
				x = re.sub(r"(\s+)?\]$", r" ]", x)
				r.append(x)
			return r

		subsearches = findSubsearches(workingString)

		for x in subsearches:
			workingString = workingString.replace(x, 'SUBSEARCHFTW')

		workingString = re.sub(r'\s+', r' ', workingString)
		workingString = re.sub(r'(?<!^)\s?\|', r'\n|', workingString)

		subsearches = formatSubSearches(subsearches)

		# Gotta put the subsearches back in.
		for x in subsearches:
			workingString = workingString.replace('SUBSEARCHFTW', x, 1)

		for x in stgs:
			workingString = workingString.replace('STRINGSTRINGSTRINGYSTRING', x, 1)

		workingString = re.sub(r"\|([^ ])", r"| \1", workingString)

		return workingString

	def run(self, edit, area_to_format='selection'):
		if area_to_format == 'selection':
			for region in self.view.sel():
				if not region.empty():
					s = self.view.substr(region)
					self.view.replace(edit, region, self.formatSplunkSearch(s))
		elif area_to_format == 'view':
			view = sublime.Region(0, self.view.size())
			s = self.view.substr(view)
			self.view.replace(edit, view, self.formatSplunkSearch(s))
