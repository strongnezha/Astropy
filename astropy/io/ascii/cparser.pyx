# Licensed under a 3-clause BSD style license - see LICENSE.rst

import six
import numpy as np
from ...utils.data import get_readable_fileobj

cdef extern from "src/tokenizer.h":
	ctypedef enum tokenizer_state:
		START_LINE
		FIELD

	ctypedef struct tokenizer_t:
		char *source		# single string containing all of the input
		int source_len 		# length of the input
		int source_pos		# current index in source for tokenization
		char delimiter		# delimiter character
		char comment		# comment character
		char quotechar		# quote character
		char **output_cols	# array of output strings for each column
		int output_len		# length of each output column string
		int *row_positions	# array of indices specifying where each row begins
		int row_pos_len		# length of row_positions array
		int num_cols		# number of table columns
		int num_rows		# number of table rows
		tokenizer_state state   # current state of the tokenizer
		int err_code		# represents the latest error that has occurred
		# Example input/output
		# --------------------
		# source: "A,B,C\n10,5.,6\n1,2,3"
		# output_cols: ["A101", "B5.2", "C6 3"]
		# row_positions: [0, 1, 3]

	tokenizer_t *create_tokenizer(char delimiter, char comment, char quotechar)
	void delete_tokenizer(tokenizer_t *tokenizer)
	int tokenize_header(tokenizer_t *self)
	int tokenize(tokenizer_t *self)

class CParserError(Exception):
	"""
	An instance of this class is thrown when an error occurs
	during C parsing.
	"""

ERR_CODES = {0: "no error",
             }

cdef class CParser:
	"""
	A fast Cython parser class which uses underlying C code
	for tokenization.
	"""

	cdef:
		tokenizer_t *tokenizer
		object source
		int header_start
		int data_start
		object include_names
		object exclude_names
		object fill_values
		object fill_include_names
		object fill_exclude_names

	cdef public:
		int width
		object names

	def __cinit__(self, source,
				  delimiter=',',
				  comment=None,
				  quotechar='"',
				  header_start=0,
				  data_start=1,
				  names=None,
				  include_names=None,
				  exclude_names=None,
				  fill_values=('', '0'),
				  fill_include_names=None,
				  fill_exclude_names=None):

		self.tokenizer = create_tokenizer(ord(delimiter), ord(comment), ord(quotechar))
		self.source = None
		self.setup_tokenizer(source)
		self.header_start = header_start
		self.data_start = data_start
		self.names = names
		self.include_names = include_names
		self.exclude_names = exclude_names
		self.fill_values = fill_values
		self.fill_include_names = fill_include_names
		self.fill_exclude_names = fill_exclude_names
	
	def __dealloc__(self):
		delete_tokenizer(self.tokenizer)

	cdef raise_error(self, msg):
		err_msg = ERR_CODES.get(self.tokenizer.err_code, "unknown error")
		raise CParserError("{}: {}".format(msg, err_msg))

	cdef setup_tokenizer(self, source):
		cdef char *src

		if isinstance(source, six.string_types):
			if '\n' not in source and '\r' not in source + '': #todo: check else case
				with get_readable_fileobj(source) as file_obj:
					source = file_obj.read()
		elif hasattr(source, 'read'): # file-like object
			source = source.read()
		else:
			try:
				source = '\n'.join(source) # iterable sequence of lines
			except TypeError:
				raise TypeError('Input "table" must be a file-like object, a string (filename'
			  			   'or data), or an iterable')
		# Create a reference to the Python object so its char * pointer remains valid
		self.source = source
		src = source
		self.tokenizer.source = src
		self.tokenizer.source_len = len(self.source)

	def read_header(self):
		# header_start is a valid line number
		if self.names:
			self.width = len(self.names)
			self.tokenizer.num_cols = self.width
		elif self.header_start is not None and self.header_start >= 0:
			if tokenize_header(self.tokenizer) != 0:
				self.raise_error("An error occurred while tokenizing the header line")
                        # TODO: self.names = ...
			self.width = self.tokenizer.num_cols
			
	def read(self):
		# TODO: use data_start
		if tokenize(self.tokenizer) != 0:
			self.raise_error("An error occurred while tokenizing data")
		return self._convert_data()

	cdef _trim(self, s): # TODO: probably move this to C using strlen
		for i, ch in enumerate(s):
			if ch == '\x00':
				return s[:i]
		return s

	cdef _convert_data(self):
		# TODO: implement conversion
		cols = {}
		for i in range(self.tokenizer.num_cols):
			cols[self.names[i]] = np.empty(self.tokenizer.num_rows, dtype=np.object_)
			for j in range(self.tokenizer.num_rows):
				if j != self.tokenizer.num_rows - 1:
					cols[self.names[i]][j] = self._trim(self.tokenizer.output_cols[i][self.tokenizer.row_positions[j] : 
																					  self.tokenizer.row_positions[j + 1]])
				else:
					cols[self.names[i]][j] = self._trim(self.tokenizer.output_cols[i][self.tokenizer.row_positions[j]:])
		return cols
