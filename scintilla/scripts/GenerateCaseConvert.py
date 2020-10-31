#!/usr/bin/env python3
# Script to generate CaseConvert.cxx from Python's Unicode data
# Should be run rarely when a Python with a new version of Unicode data is available.

# Current best approach divides case conversions into two cases:
# simple symmetric and complex.
# Simple symmetric is where a lower and upper case pair convert to each
# other and the folded form is the same as the lower case.
# There are 1006 symmetric pairs.
# These are further divided into ranges (stored as lower, upper, range length,
# range pitch and singletons (stored as lower, upper).
# Complex is for cases that don't fit the above: where there are multiple
# characters in one of the forms or fold is different to lower or
# lower(upper(x)) or upper(lower(x)) are not x. These are represented as UTF-8
# strings with original, folded, upper, and lower separated by '|'.
# There are 126 complex cases.

import sys
import platform
import unicodedata
import io
import itertools
import string
from pprint import pprint

from FileGenerator import Regenerate
from GenerateCharacterCategory import compressIndexTable

UnicodeCharacterCount = sys.maxunicode + 1

def getCharName(ch):
	try:
		return unicodedata.name(ch).title()
	except ValueError:
		return ''

def isCaseSensitive(ch):
	return ch != ch.upper() or ch != ch.lower() or ch != ch.casefold()

def contiguousRanges(l, diff):
	# l is s list of lists
	# group into lists where first element of each element differs by diff
	out = [[l[0]]]
	for s in l[1:]:
		if s[0] != out[-1][-1][0] + diff:
			out.append([])
		out[-1].append(s)
	return out

def flatten(listOfLists):
	"Flatten one level of nesting"
	return itertools.chain.from_iterable(listOfLists)

def conversionSets():
	# For all Unicode characters, see whether they have case conversions
	# Return 2 sets: one of simple symmetric conversion cases and another
	# with complex cases.
	complexes = []
	symmetrics = []
	for ch in range(UnicodeCharacterCount):
		if ch >= 0xd800 and ch <= 0xDBFF:
			continue
		if ch >= 0xdc00 and ch <= 0xDFFF:
			continue
		uch = chr(ch)

		fold = uch.casefold()
		upper = uch.upper()
		lower = uch.lower()
		symmetric = False
		if uch != upper and len(upper) == 1 and uch == lower and uch == fold:
			lowerUpper = upper.lower()
			foldUpper = upper.casefold()
			if lowerUpper == foldUpper and lowerUpper == uch:
				symmetric = True
				symmetrics.append((ch, ord(upper), ch - ord(upper)))
		if uch != lower and len(lower) == 1 and uch == upper and lower == fold:
			upperLower = lower.upper()
			if upperLower == uch:
				symmetric = True

		if fold == uch:
			fold = ""
		if upper == uch:
			upper = ""
		if lower == uch:
			lower = ""

		if (fold or upper or lower) and not symmetric:
			complexes.append((uch, fold, upper, lower))

	return symmetrics, complexes

def groupRanges(symmetrics):
	# Group the symmetrics into groups where possible, returning a list
	# of ranges and a list of symmetrics that didn't fit into a range

	def distance(s):
		return s[2]

	groups = []
	uniquekeys = []
	for k, g in itertools.groupby(symmetrics, distance):
		groups.append(list(g))      # Store group iterator as a list
		uniquekeys.append(k)

	contiguousGroups = flatten([contiguousRanges(g, 1) for g in groups])
	longGroups = [(x[0][0], x[0][1], len(x), 1) for x in contiguousGroups if len(x) > 4]

	oneDiffs = [s for s in symmetrics if s[2] == 1]
	contiguousOnes = flatten([contiguousRanges(g, 2) for g in [oneDiffs]])
	longOneGroups = [(x[0][0], x[0][1], len(x), 2) for x in contiguousOnes if len(x) > 4]

	rangeGroups = sorted(longGroups+longOneGroups, key=lambda s: s[0])

	rangeCoverage = list(flatten([range(r[0], r[0]+r[2]*r[3], r[3]) for r in rangeGroups]))

	nonRanges = [(l, u) for l, u, d in symmetrics if l not in rangeCoverage]

	return rangeGroups, nonRanges

def escape(s):
	return "".join((chr(c) if chr(c) in string.ascii_letters else "\\x%x" % c) for c in s.encode('utf-8'))

def updateCaseConvert():
	symmetrics, complexes = conversionSets()

	rangeGroups, nonRanges = groupRanges(symmetrics)

	print(len(rangeGroups), "ranges")
	rangeLines = ["%d,%d,%d,%d," % x for x in rangeGroups]

	print(len(nonRanges), "non ranges")
	nonRangeLines = ["%d,%d," % x for x in nonRanges]

	print(len(symmetrics), "symmetric")

	complexLines = ['"%s|%s|%s|%s|"' % tuple(escape(t) for t in x) for x in complexes]
	print(len(complexLines), "complex")

	Regenerate("../src/CaseConvert.cxx", "//", rangeLines, nonRangeLines, complexLines)

def getUnicodeCaseSensitivityGroup(caseList):
	ranges = []
	count = len(caseList)
	start = 0
	while start < count:
		index = start
		while index + 1 < count and caseList[index][0] + 1 == caseList[index + 1][0]:
			index += 1
		begin = caseList[start]
		end = caseList[index]
		begin = begin[0]
		end = end[0]
		ranges.append((begin, end, end - begin + 1, hex(begin), hex(end)))
		start = index + 1

	groups = []
	count = len(ranges)
	start = 0
	total_size = 0
	header_size = 3*4
	while start < count:
		index = start
		while index + 1 < count and ranges[index][1] + 256 >= ranges[index + 1][0]:
			index += 1
		items = ranges[start:index + 1]
		size = header_size
		begin = items[0][0]
		end = items[-1][1]
		if len(items) == 1:
			end += 1
		else:
			if begin < 256:
				begin = 0
				size -= header_size
			word = (end - begin + 32) // 32
			end = begin + 32*word
			size += 4*word
		total_size += size
		groups.append({
			'min': begin,
			'min_hex': hex(begin),
			'max': end,
			'max_hex': hex(end),
			'size': (size, header_size*len(items)),
			'count': sum(item[2] for item in items),
			'ranges': items
		})
		start = index + 1

	print('Unicode Case Sensitivity ranges:', len(groups), 'size:', total_size)
	return groups

def checkUnicodeCaseSensitivity(filename=None):
	caseList = []
	caseTable = ['0']*UnicodeCharacterCount

	for ch in range(UnicodeCharacterCount):
		uch = chr(ch)
		if isCaseSensitive(uch):
			caseList.append((ch, hex(ch), uch, getCharName(uch)))
			caseTable[ch] = '1'

	print(len(caseList), caseList[-1])
	groups = getUnicodeCaseSensitivityGroup(caseList)

	with open('caseList.log', 'w', encoding='utf-8') as fd:
		output = io.StringIO()
		output.write('caseList:\n')
		pprint(caseList, stream=output, width=150)
		output.write('\ngroups:\n')
		pprint(groups, stream=output, width=80)
		fd.write(output.getvalue())

	if not filename:
		return

	output = ["// Created with Python %s, Unicode %s" % (
		platform.python_version(), unicodedata.unidata_version)]

	maskTable = []
	first = groups[0]['max']
	maxCh = caseList[-1][0]

	for i in range(0, first, 32):
		mask = int(''.join(reversed(caseTable[i:i+32])), 2)
		maskTable.append(mask)

	output.append('#define kUnicodeCaseSensitiveFirst\t0x%04xU' % first)
	output.append('#define kUnicodeCaseSensitiveMax\t0x%04xU' % maxCh)
	output.append('')

	output.append('static const UnicodeCaseSensitivityRange UnicodeCaseSensitivityRangeList[] = {')
	for group in groups[1:]:
		minCh = group['min']
		maxCh = group['max']
		if len(group['ranges']) == 1:
			output.append('\t{ 0x%04x, 0x%04x, 0 },' % (minCh, maxCh))
		else:
			output.append('\t{ 0x%04x, 0x%04x, %d },' % (minCh, maxCh, len(maskTable)))
			for i in range(minCh, maxCh, 32):
				mask = int(''.join(reversed(caseTable[i:i+32])), 2)
				maskTable.append(mask)
	output.append('};')
	output.append('')

	output.append('static const uint32_t UnicodeCaseSensitivityMask[] = {')
	for i in range(0, len(maskTable), 8):
		line = ', '.join('0x%08xU' % mask for mask in maskTable[i:i+8])
		output.append(line + ',')
	output.append('};')
	output.append('')

	with open(filename, 'w', encoding='utf-8') as fd:
		fd.write(r"""#include <stdint.h>

#define COUNTOF(a)		(sizeof(a) / sizeof(a[0]))

typedef struct UnicodeCaseSensitivityRange {
	uint32_t low;
	uint32_t high;
	uint32_t offset;
} UnicodeCaseSensitivityRange;

""")
		fd.write('\n'.join(output))
		fd.write(r"""
int IsCharacterCaseSensitive(uint32_t ch) {
	if (ch < kUnicodeCaseSensitiveFirst) {
		return (UnicodeCaseSensitivityMask[ch >> 5] >> (ch & 31)) & 1;
	}
	for (uint32_t index = 0; index < COUNTOF(UnicodeCaseSensitivityRangeList); index++) {
		const UnicodeCaseSensitivityRange range = UnicodeCaseSensitivityRangeList[index];
		if (ch < range.high) {
			if (ch < range.low) {
				return 0;
			}
			if (range.offset)  {
				ch -= range.low;
				return (UnicodeCaseSensitivityMask[range.offset + (ch >> 5)] >> (ch & 31)) & 1;
			}
			return 1;
		}
	}
	return 0;
}

#if 1
#include <stdio.h>

""")

		output = []
		maxCh = groups[-1]['max']
		output.append('static const uint8_t UnicodeCaseSensitivityTable[] = {')
		for i in range(0, maxCh, 64):
			line = ','.join(caseTable[i:i+64])
			output.append(line + ',')
		output.append('};')
		output.append('')
		fd.write('\n'.join(output))

		fd.write(r"""
int main(void) {
	for (uint32_t ch = 0; ch < COUNTOF(UnicodeCaseSensitivityTable); ch++) {
		const int result = IsCharacterCaseSensitive(ch);
		const int expect = UnicodeCaseSensitivityTable[ch];
		if (result != expect) {
			printf("case diff: %u %04x %d %d\n", ch, ch, result, expect);
			break;
		}
	}
	return 0;
}

#endif
""")

def updateCaseSensitivity(filename, test=False):
	caseTable = ['0']*UnicodeCharacterCount
	maskTable = [0] * (UnicodeCharacterCount >> 5)
	first = 0x600
	maxCh = 0

	for ch in range(UnicodeCharacterCount):
		if isCaseSensitive(chr(ch)):
			maxCh = ch
			caseTable[ch] = '1'
			maskTable[ch >> 5] |= (1 << (ch & 31))

	count = 1 + (maxCh >> 5)
	maskList = maskTable[:(first >> 5)]
	maskTable = maskTable[len(maskList):count]
	indexTable = []
	for mask in maskTable:
		try:
			index = maskList.index(mask)
		except ValueError:
			index = len(maskList)
			maskList.append(mask)
		indexTable.append(index)

	print('Unicode Case Sensitivity maskList:', len(maskList), 'indexTable:', len(indexTable), count, maxCh)

	args = {
		'table': 'UnicodeCaseSensitivityIndex',
		'with_function': False,
	}

	table, function = compressIndexTable('Unicode Case Sensitivity', indexTable, args)
	table = 'static ' + table

	output = ["// Created with Python %s, Unicode %s" % (
		platform.python_version(), unicodedata.unidata_version)]

	output.append('#define kUnicodeCaseSensitiveFirst\t0x%04xU' % first)
	output.append('#define kUnicodeCaseSensitiveMax\t0x%04xU' % maxCh)
	output.append('')
	output.extend(table.splitlines())
	output.append('')

	output.append('static const uint32_t UnicodeCaseSensitivityMask[] = {')
	for i in range(0, len(maskList), 8):
		line = ', '.join('0x%08xU' % mask for mask in maskList[i:i+8])
		output.append(line + ',')
	output.append('};')

	function = """
// case sensitivity for ch in [kUnicodeCaseSensitiveFirst, kUnicodeCaseSensitiveMax)
static inline int IsCharacterCaseSensitiveSecond(uint32_t ch) {{
	const uint32_t lower = ch & 31;
	ch = (ch - kUnicodeCaseSensitiveFirst) >> 5;
	ch = ({table}[ch >> {shiftA}] << {shiftA2}) | (ch & {maskA});
	ch = ({table}[{offsetC} + (ch >> {shiftC})] << {shiftC2}) | (ch & {maskC});
	ch = {table}[{offsetD} + ch];
	return (UnicodeCaseSensitivityMask[ch] >> lower) & 1;
}}
""".format(**args)
	output.extend(function.splitlines())

	if not test:
		Regenerate(filename, "//case", output)
		return

	with open(filename, 'w', encoding='utf-8') as fd:
		fd.write(r"""#include <stdint.h>
""")
		fd.write('\n'.join(output))
		fd.write(r"""

int IsCharacterCaseSensitive(uint32_t ch)	{
	if (ch < kUnicodeCaseSensitiveFirst) {
		return (UnicodeCaseSensitivityMask[ch >> 5] >> (ch & 31)) & 1;
	}
	if (ch > kUnicodeCaseSensitiveMax) {
		return 0;
	}
	return IsCharacterCaseSensitiveSecond(ch);
}

#if 1
""")

		count *= 32
		output = []
		output.append('static const uint8_t UnicodeCaseSensitivityTable[] = {')
		for i in range(0, count, 64):
			line = ','.join(caseTable[i:i+64])
			output.append(line + ',')
		output.append('};')
		output.append('')
		fd.write('\n'.join(output))

		fd.write(r"""
#include <stdio.h>
#define COUNTOF(a)		(sizeof(a) / sizeof(a[0]))

int main(void) {
	for (uint32_t ch = 0; ch < COUNTOF(UnicodeCaseSensitivityTable); ch++) {
		const int result = IsCharacterCaseSensitive(ch);
		const int expect = UnicodeCaseSensitivityTable[ch];
		if (result != expect) {
			printf("case diff: %u %04x %d %d\n", ch, ch, result, expect);
			break;
		}
	}
	return 0;
}

#endif
""")

updateCaseConvert()
#checkUnicodeCaseSensitivity('caseList.c')
#updateCaseSensitivity('CaseSensitivity.c', True)
updateCaseSensitivity('../../src/EditEncoding.c')
