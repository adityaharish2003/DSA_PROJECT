import heapq
import os
import pickle

class HuffmanCoding:
	def __init__(self, path):
		self.path = path
		self.heap = []
		self.codes = {}
		self.reverse_mapping = {}
		self.delimiter = '\x01'
		self.delimiter += '\x02'
		self.delimiter += '\x03'

	class HeapNode:
		def __init__(self, char, freq):
			self.char = char
			self.freq = freq
			self.left = None
			self.right = None

		# defining comparators less_than and equals
		def __lt__(self, other):
			return self.freq < other.freq

		def __eq__(self, other):
			if(other == None):
				return False
			if(not isinstance(other, HeapNode)):
				return False
			return self.freq == other.freq

	# functions for compression:

	def make_frequency_dict(self, text):
		frequency = {}
		for character in text:
			if not character in frequency:
				frequency[character] = 0
			frequency[character] += 1
		return frequency

	def make_heap(self, frequency):
		for key in frequency:
			node = self.HeapNode(key, frequency[key])
			heapq.heappush(self.heap, node)

	def merge_nodes(self):
		while(len(self.heap) > 1):
			node1 = heapq.heappop(self.heap)
			node2 = heapq.heappop(self.heap)

			merged = self.HeapNode(None, node1.freq + node2.freq)
			merged.left = node1
			merged.right = node2

			heapq.heappush(self.heap, merged)


	def make_codes_helper(self, root, current_code):
		if(root == None):
			return

		if(root.char != None):
			self.codes[root.char] = current_code
			self.reverse_mapping[current_code] = root.char
			return

		self.make_codes_helper(root.left, current_code + "0")
		self.make_codes_helper(root.right, current_code + "1")


	def make_codes(self):
		root = heapq.heappop(self.heap)
		current_code = ""
		self.make_codes_helper(root, current_code)


	def get_encoded_text(self, text):
		encoded_text = ""
		for character in text:
			encoded_text += self.codes[character]
		return encoded_text


	def pad_encoded_text(self, encoded_text):
		extra_padding = 8 - len(encoded_text) % 8
		for i in range(extra_padding):
			encoded_text += "0"

		padded_info = "{0:08b}".format(extra_padding)
		encoded_text = padded_info + encoded_text
		return encoded_text


	def get_byte_array(self, padded_encoded_text):
		if(len(padded_encoded_text) % 8 != 0):
			print("Encoded text not padded properly")
			exit(0)

		b = bytearray()
		for i in range(0, len(padded_encoded_text), 8):
			byte = padded_encoded_text[i:i+8]
			b.append(int(byte, 2))
		return b


	def compress(self,file_ext = '.txt',shape = 0):

		filename, file_extension = os.path.splitext(self.path)
		output_path = filename + ".bin"
		file_extension = file_ext
		with open(self.path, 'r+' , encoding = 'latin1') as file, open(output_path, 'wb') as output:
			text = file.read()
			text = text.rstrip()
			frequency = self.make_frequency_dict(text)
			self.make_heap(frequency)
			self.merge_nodes()
			self.make_codes()
			encoded_text = self.get_encoded_text(text)
			padded_encoded_text = self.pad_encoded_text(encoded_text)
			print(len(self.codes))
			b = self.get_byte_array(padded_encoded_text)
			output.write(bytes(b))
			delimiter =  bytes(self.delimiter,'latin1')
			output.write(delimiter)
			output.write(bytes((' '.join('{0:08b}'.format(ord(x), 'b') for x in file_extension)),'latin1'))
			output.write(bytes('\x01','latin1'))
			self.codes["shape"] = shape
			pickle.dump(self.codes, output)
		print("Compressed")
		return output_path


	""" functions for decompression: """


	def remove_padding(self, padded_encoded_text):
		padded_info = padded_encoded_text[:8]
		extra_padding = int(padded_info, 2)

		padded_encoded_text = padded_encoded_text[8:] 
		encoded_text = padded_encoded_text[:-1*extra_padding]

		return encoded_text

	def decode_text(self, encoded_text):
		current_code = ""
		decoded_text = ""

		for bit in encoded_text:
			current_code += bit
			if(current_code in self.reverse_mapping):
				character = self.reverse_mapping[current_code]
				decoded_text += character
				current_code = ""

		return decoded_text


	def decompress(self):
		filename, file_extension = os.path.splitext(self.path)
		output_path = filename  + "_unc" + ".txt"
		file_extension = ""
		huff_code = {}
		delimiter = [bytes('\x01','latin1'),bytes('\x02','latin1'),bytes('\x03','latin1')]
		with open(self.path, 'rb') as file, open(output_path, 'w',encoding='latin1') as output:
			bit_string = ""
			byte = file.read(1)
			shape = 0
			while(True):
			# while(len(byte) > 0 and byte != bytes(' '.join('{0:08b}'.format(ord(x), 'b') for x in delimiter),encoding= 'utf-8')):
				while(len(byte) >0 and byte != delimiter[0]):
					byte = ord(byte)
					bits = bin(byte)[2:].rjust(8, '0')
					bit_string += bits
					byte = file.read(1)
				char1 = file.read(1)
				char2 = ''
				if(char1 == delimiter[1]):
					char2 = file.read(1)
					if(char2 == delimiter[2]):
						break
					else:
						char1 = ord(char1)
						bits = bin(char1)[2:].rjust(8, '0')
						bit_string += bits
						char2 = ord(char2)
						bits = bin(char2)[2:].rjust(8, '0')
						bit_string += bits
						byte = file.read(1)
				else :
					char1= ord(char1)
					bits = bin(char1)[2:].rjust(8, '0')
					bit_string += bits
					byte = file.read(1)

			encoded_text = self.remove_padding(bit_string)
			byte = file.read(1)
			# while(len(byte) > 0 and (byte) != bytes(' '.join('{0:08b}'.format(ord(x), 'b') for x in delimiter),encoding= 'utf-8')):
			while(len(byte) >0 and byte != delimiter[0]):
				file_extension += chr(ord(byte))
				byte = file.read(1)
			file_extension = [chr(int(i,2)) for i in file_extension.split()]
			file_extension = ''.join(file_extension)
			huff_code = pickle.load(file,encoding='latin1')
			shape = huff_code.pop("shape")
			# rev_huff_code = {v:k for k,v in codes.items()}
			rev_huff_code = {v:k for k,v in huff_code.items()}
			self.reverse_mapping = rev_huff_code

			decompressed_text = self.decode_text(encoded_text)
			output.write(decompressed_text)

		print("Decompressed")
		return output_path,file_extension,shape