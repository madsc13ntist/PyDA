from capstone import *
from helpers import *
from ctypes import *
from struct import unpack

def disassemble(binary):
    return PE(binary)
#except: return False


# The parsing logic below is blatantly ripped off of ROPGadget v5.0:
# PE class =========================================================================================

class PEFlags:
        IMAGE_MACHINE_INTEL_386       = 0x014c
        IMAGE_MACHINE_AMD_8664        = 0x8664
        IMAGE_FILE_MACHINE_ARM        = 0x1c0
        IMAGE_NT_OPTIONAL_HDR32_MAGIC = 0x10b
        IMAGE_NT_OPTIONAL_HDR64_MAGIC = 0x20b
        IMAGE_SIZEOF_SHORT_NAME       = 0x8

# tableau (c_char * 32)

class IMAGE_FILE_HEADER(Structure):
    _fields_ =  [
                    ("Magic",                       c_uint),
                    ("Machine",                     c_ushort),
                    ("NumberOfSections",            c_ushort),
                    ("TimeDateStamp",               c_uint),
                    ("PointerToSymbolTable",        c_uint),
                    ("NumberOfSymbols",             c_uint),
                    ("SizeOfOptionalHeader",        c_ushort),
                    ("Characteristics",             c_ushort)
                ]

class IMAGE_OPTIONAL_HEADER(Structure):
    _fields_ =  [
                    ("Magic",                       c_ushort),
                    ("MajorLinkerVersion",          c_ubyte),
                    ("MinorLinkerVersion",          c_ubyte),
                    ("SizeOfCode",                  c_uint),
                    ("SizeOfInitializedData",       c_uint),
                    ("SizeOfUninitializedData",     c_uint),
                    ("AddressOfEntryPoint",         c_uint),
                    ("BaseOfCode",                  c_uint),
                    ("BaseOfData",                  c_uint),
                    ("ImageBase",                   c_uint),
                    ("SectionAlignment",            c_uint),
                    ("FileAlignment",               c_uint),
                    ("MajorOperatingSystemVersion", c_ushort),
                    ("MinorOperatingSystemVersion", c_ushort),
                    ("MajorImageVersion",           c_ushort),
                    ("MinorImageVersion",           c_ushort),
                    ("MajorSubsystemVersion",       c_ushort),
                    ("MinorSubsystemVersion",       c_ushort),
                    ("Win32VersionValue",           c_uint),
                    ("SizeOfImage",                 c_uint),
                    ("SizeOfHeaders",               c_uint),
                    ("CheckSum",                    c_uint),
                    ("Subsystem",                   c_ushort),
                    ("DllCharacteristics",          c_ushort),
                    ("SizeOfStackReserve",          c_uint),
                    ("SizeOfStackCommit",           c_uint),
                    ("SizeOfHeapReserve",           c_uint),
                    ("SizeOfHeapCommit",            c_uint),
                    ("LoaderFlags",                 c_uint),
                    ("NumberOfRvaAndSizes",         c_uint)
                ]

class IMAGE_OPTIONAL_HEADER64(Structure):
    _fields_ =  [
                    ("Magic",                       c_ushort),
                    ("MajorLinkerVersion",          c_ubyte),
                    ("MinorLinkerVersion",          c_ubyte),
                    ("SizeOfCode",                  c_uint),
                    ("SizeOfInitializedData",       c_uint),
                    ("SizeOfUninitializedData",     c_uint),
                    ("AddressOfEntryPoint",         c_uint),
                    ("BaseOfCode",                  c_uint),
                    ("BaseOfData",                  c_uint),
                    ("ImageBase",                   c_ulonglong),
                    ("SectionAlignment",            c_uint),
                    ("FileAlignment",               c_uint),
                    ("MajorOperatingSystemVersion", c_ushort),
                    ("MinorOperatingSystemVersion", c_ushort),
                    ("MajorImageVersion",           c_ushort),
                    ("MinorImageVersion",           c_ushort),
                    ("MajorSubsystemVersion",       c_ushort),
                    ("MinorSubsystemVersion",       c_ushort),
                    ("Win32VersionValue",           c_uint),
                    ("SizeOfImage",                 c_uint),
                    ("SizeOfHeaders",               c_uint),
                    ("CheckSum",                    c_uint),
                    ("Subsystem",                   c_ushort),
                    ("DllCharacteristics",          c_ushort),
                    ("SizeOfStackReserve",          c_ulonglong),
                    ("SizeOfStackCommit",           c_ulonglong),
                    ("SizeOfHeapReserve",           c_ulonglong),
                    ("SizeOfHeapCommit",            c_ulonglong),
                    ("LoaderFlags",                 c_uint),
                    ("NumberOfRvaAndSizes",         c_uint)
                ]

class IMAGE_NT_HEADERS(Structure):
    _fields_ =  [
                    ("Signature",       c_uint),
                    ("FileHeader",      IMAGE_FILE_HEADER),
                    ("OptionalHeader",  IMAGE_OPTIONAL_HEADER)
                ]

class IMAGE_NT_HEADERS64(Structure):
    _fields_ =  [
                    ("Signature",       c_uint),
                    ("FileHeader",      IMAGE_FILE_HEADER),
                    ("OptionalHeader",  IMAGE_OPTIONAL_HEADER64)
                ]

class IMAGE_SECTION_HEADER(Structure):
    _fields_ =  [
                    ("Name",                    c_ubyte * PEFlags.IMAGE_SIZEOF_SHORT_NAME),
                    ("PhysicalAddress",         c_uint),
                    ("VirtualAddress",          c_uint),
                    ("SizeOfRawData",           c_uint),
                    ("PointerToRawData",        c_uint),
                    ("PointerToRelocations",    c_uint),
                    ("PointerToLinenumbers",    c_uint),
                    ("NumberOfRelocations",     c_ushort),
                    ("NumberOfLinenumbers",     c_ushort),
                    ("Characteristics",         c_uint)
                ]

""" This class parses the PE format """
class PE:
    FILETYPE_NAME = 'PE'
    def __init__(self, binary):
        self.__binary = bytearray(binary)

        self.__PEOffset              = 0x00000000
        self.__IMAGE_FILE_HEADER     = None
        self.__IMAGE_OPTIONAL_HEADER = None

        self.__sections_l = []
        self.__getPEOffset()
        self.__parsePEHeader()
        self.__parseOptHeader()
        self.__parseSections()

    def __getPEOffset(self):
        self.__PEOffset = unpack("<I", str(self.__binary[60:64]))[0]
        print "self.__PEOffset", self.__PEOffset
        if self.__binary[self.__PEOffset:self.__PEOffset+4] != "50450000".decode("hex"):
            print "[Error] PE.__getPEOffset() - Bad PE signature"
            raise BadMagicHeaderException()

    def __parsePEHeader(self):
        PEheader = self.__binary[self.__PEOffset:]
        self.__IMAGE_FILE_HEADER = IMAGE_FILE_HEADER.from_buffer_copy(PEheader)

    def __parseOptHeader(self):
        PEoptHeader = self.__binary[self.__PEOffset+24:self.__PEOffset+24+self.__IMAGE_FILE_HEADER.SizeOfOptionalHeader]

        if unpack("<H", str(PEoptHeader[0:2]))[0] == PEFlags.IMAGE_NT_OPTIONAL_HDR32_MAGIC:
            self.__IMAGE_OPTIONAL_HEADER = IMAGE_OPTIONAL_HEADER.from_buffer_copy(PEoptHeader)

        elif unpack("<H", str(PEoptHeader[0:2]))[0] == PEFlags.IMAGE_NT_OPTIONAL_HDR64_MAGIC:
            self.__IMAGE_OPTIONAL_HEADER = IMAGE_OPTIONAL_HEADER64.from_buffer_copy(PEoptHeader)

        else:
            print "[Error] PE.__parseOptHeader - Bad size header"
            raise BadMagicHeaderException()

    def __parseSections(self):
        baseSections = self.__PEOffset+24+self.__IMAGE_FILE_HEADER.SizeOfOptionalHeader
        sizeSections = self.__IMAGE_FILE_HEADER.NumberOfSections * sizeof(IMAGE_SECTION_HEADER)
        base = self.__binary[baseSections:baseSections+sizeSections]

        for i in range(self.__IMAGE_FILE_HEADER.NumberOfSections):
            sec = IMAGE_SECTION_HEADER.from_buffer_copy(base)
            base = base[sizeof(IMAGE_SECTION_HEADER):]
            self.__sections_l += [sec]

        return 0

    def getEntryPoint(self):
        return self.__IMAGE_OPTIONAL_HEADER.ImageBase + self.__IMAGE_OPTIONAL_HEADER.AddressOfEntryPoint

    def getDataSections(self):
        ret = []
        for section in self.__sections_l:
            if section.Characteristics & 0x80000000:
                ret +=  [{
                            "name"    : ''.join([chr(x) for x in section.Name]),
                            "offset"  : section.PointerToRawData,
                            "size"    : section.SizeOfRawData,
                            "vaddr"   : section.VirtualAddress + self.__IMAGE_OPTIONAL_HEADER.ImageBase,
                            "opcodes" : str(self.__binary[section.PointerToRawData:section.PointerToRawData+section.SizeOfRawData])
                        }]
        return ret

    def getExecSections(self):
        ret = []
        for section in self.__sections_l:
            if section.Characteristics & 0x20000000:
                ret +=  [{
                            "name"    : ''.join([chr(x) for x in section.Name]),
                            "offset"  : section.PointerToRawData,
                            "size"    : section.SizeOfRawData,
                            "vaddr"   : section.VirtualAddress + self.__IMAGE_OPTIONAL_HEADER.ImageBase,
                            "opcodes" : str(self.__binary[section.PointerToRawData:section.PointerToRawData+section.SizeOfRawData])
                        }]
        return ret

    def getArch(self):
        if self.__IMAGE_FILE_HEADER.Machine ==  PEFlags.IMAGE_MACHINE_INTEL_386 or self.__IMAGE_FILE_HEADER.Machine == PEFlags.IMAGE_MACHINE_AMD_8664:
            return CS_ARCH_X86
        if self.__IMAGE_FILE_HEADER.Machine == PEFlags.IMAGE_FILE_MACHINE_ARM:
            return CS_ARCH_ARM
        else:
            print "[Error] PE.getArch() - Bad Arch"
            sys.exit(-1)

    def getArchMode(self):
        if self.__IMAGE_OPTIONAL_HEADER.Magic == PEFlags.IMAGE_NT_OPTIONAL_HDR32_MAGIC:
            return CS_MODE_32
        elif self.__IMAGE_OPTIONAL_HEADER.Magic == PEFlags.IMAGE_NT_OPTIONAL_HDR64_MAGIC:
            return CS_MODE_64
        else:
            print "[Error] PE.getArch() - Bad arch size"
            sys.exit(-1)

    def getFormat(self):
        return "PE"

    def disassemble(self):
        md = capstone.Cs(self.getArch(), self.getArchMode())
        disassembly = CommonProgramDisassemblyFormat(PE.PROGRAM_INFO)

        for s in self.getExecSections():
            if s["name"] in PE.dont_disassemble:
                continue
            
            s["name"] = s["name"].replace('\x00','')
            section = CommonSectionFormat(s["name"])

            for inst in md.disasm(s["opcodes"], s["vaddr"]):
                section.addInst(CommonInstFormat(inst.address, inst.mnemonic, inst.op_str))

            section.searchForFunctions()
            disassembly.addSection(section)
        return disassembly


    PROGRAM_INFO = '''
    ##############################################
    ###     PE Information                     ###
    ###     Executable:                        ###
    ###     More stuff from the beginning      ###
    ##############################################
    '''

    dont_disassemble = ['.comment','.shstrtab','.symtab','.strtab','.note.ABI-tag','.note.gnu.build-id','.hash','.gnu.hash','.dynsym','.dynstr','.gnu.version','.gnu.version_r','.rodata','.eh_frame','.init_array','.jcr','.dynamic','.got','.got.plt','.data','.bss','.interp','.eh_frame_hdr','.plt','.init','.rel.plt','.rel.dyn']
