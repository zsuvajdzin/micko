"""
1. (codegen) indent bi mozda trebalo da se zove new_line
2. posto se za (skoro) svaki od tipova id-jeva mora proveravati razlicit podskup kind-ova
   (npr. za funkcije treba proveravati FUNCTION i GLOBAL_VAR, za parametre samo PARAMETER),
   mozda bi bilo zgodno da se napravi jedna opsta insert_id funkcija, i onda dodatne helper
   funkcije (insert_global_var, insert_local_var, insert_constant, insert_function, insert_parameter)
   koje bi samo pozivale insert_id sa predefinisanim parametrima
3. ckeck_types -> same_types

4. generalizovati codegenerator: file_begin file_end code_begin code_end data_begin data_end jump push pop...
5. izdvojiti sve deljene podatke u shareddata
6. try za pristupe tabeli simbola
"""

from pyparsing import *

DEBUG = 0

class Enumerate(dict):
    """C enum emulation (original by Scott David Daniels)"""
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)
            self[number] = name

#############################################################################################################################
#############################################################################################################################

class SharedData(object):
    def __init__(self):
        self.functon_index = 0
        self.function_params = 0
        self.function_vars = 0
        self.loc = 0
        self.text = ""

    def setpos(self,loc,text):
        self.loc = loc
        self.text = text

#############################################################################################################################
#############################################################################################################################

class SemanticException(Exception):
    """Exception for semantic errors found during parsing, similar to ParseException.
       Introduced because ParseException is used internally in pyparsing and custom
       messages got lost and replaced by generic errors.
    """
    def __init__(self, msg=None, loc=None, text=None):
        """msg  - error message
           loc  - location (character position) of error
           text - text being parsed
        """
        super(SemanticException,self).__init__()
        self.msg = msg
        self.loc = loc
        if loc != None:
            self.line = lineno(loc, text)
            self.col = col(loc, text)
            self.text = line(loc, text)
        else:
            self.line = self.col = self.text = None
    def __str__(self):
        """String representation of semantic error"""
        msg = self.msg
        if self.line != None:
            #marker = "".join( [self.text[:self.col-1], ">!<", self.text[self.col-1:]]) 
            msg = msg + " at line:%d, col:%d\n%s" % (self.line, self.col, self.text)
        return msg

#############################################################################################################################
#############################################################################################################################

class SymbolTableEntry(object):
    """Class for one symbol table entry."""
    def __init__(self, sname = "", skind = 0, stype = 0, sattr = None, sattr_name = "None"):
        """Initialization of symbol table entry.
           sname - symbol name
           skind - symbol kind
           stype - symbol type
           sattr - symbol attribute
           sattr_name - symbol attribute name (for display only)
        """
        self.name = sname
        self.kind = skind
        self.type = stype
        self.attribute = sattr
        self.attribute_name = sattr_name
        self.param_types = []

    def set_attribute(self, name, value):
        """Sets attribute's name and value"""
        self.attribute_name = name
        self.attribute = value
    
    def attribute_str(self):
        """Returns attribute string (for display only)"""
        return "{0}={1}".format(self.attribute_name, self.attribute) if self.attribute != None else "None"

class SymbolTable(object):
    """Class for symbol table of microC program"""

    #Possible kinds of symbol table entries.
    kinds = Enumerate("NO_KIND WORKING_REGISTER GLOBAL_VAR FUNCTION PARAMETER LOCAL_VAR CONSTANT")
    #Possible types of functions and variables.
    types = Enumerate("NO_TYPE INT UNSIGNED")

    def __init__(self):
        """Initialization of symbol table"""
        super(SymbolTable,self).__init__()
        self.table = []
        self.lable_len = 0
        for reg in range(CodeGenerator.FUNCTION_REGISTER+1):
            self.insert_symbol(CodeGenerator.registers[reg], self.kinds.WORKING_REGISTER, self.types.NO_TYPE)
        #compiler data
        self.compiler = None
        #self.display()

    def display(self):
        """Displays symbol table content."""
        sym_name = "Symbol name"
        sym_len = max(max(len(i.name) for i in self.table),len(sym_name))
        kind_name = "Kind"
        kind_len = max(max(len(self.kinds[i.kind]) for i in self.table),len(kind_name))
        type_name = "Type"
        type_len = max(max(len(self.types[i.type]) for i in self.table),len(type_name))
        attr_name = "Attribute"
        attr_len = max(max(len(i.attribute_str()) for i in self.table),len(attr_name))
        print "{0:3s} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}} | {9:s}".format(" No", sym_name, sym_len, kind_name, kind_len, type_name, type_len, attr_name, attr_len, "Parameters")
        print "-----------------------------" + "-" * (sym_len + kind_len + type_len + attr_len)
        for i,sym in enumerate(self.table):
            parameters = ""
            for p in sym.param_types:
                if parameters == "":
                    parameters = "{0}".format(self.types[p])
                else:
                    parameters += ", {0}".format(self.types[p])
            print "{0:3d} | {1:^{2}s} | {3:^{4}s} | {5:^{6}s} | {7:^{8}} | ({9})".format(i, sym.name, sym_len, self.kinds[sym.kind], kind_len, self.types[sym.type], type_len, sym.attribute_str(), attr_len, parameters)

    def insert_symbol(self, sname, skind, stype):
        """Inserts new symbol at the end of symbol table.
           sname - symbol name
           skind - symbol kind
           stype - symbol type
        """
        self.table.append(SymbolTableEntry(sname, skind, stype))
        self.table_len = len(self.table)
        return self.table_len-1

    def clear_symbols(self, index):
        """Clears all symbols from index to the end of table"""
        del self.table[index:]
        self.table_len = len(self.table)

    def lookup_symbol(self, sname, skind=kinds.keys(), stype=types.keys(), debug=False):
        """Searches for symbol, from the end to beginnig.
           Returns symbol index or None
           sname - symbol name
           skind - symbol kind (one kind, list of kinds, or None) deafult: any kind
           stype - symbol type (or None) default: any type
        """
        skind = skind if isinstance(skind, list) else [skind]
        stype = stype if isinstance(stype, list) else [stype]
        if debug:
            print "\nNAME:",sname
            print "KIND:",skind
            print "TYPE:",stype
        for i, sym in [[x, self.table[x]] for x in range(len(self.table) - 1, CodeGenerator.LAST_WORKING_REGISTER, -1)]:
            if debug:
                print i, sym.name, sym.kind, sym.type, (sym.name == sname), (sym.kind in skind), (sym.type in stype)
            if (sym.name == sname) and (sym.kind in skind) and (sym.type in stype):
                return i
        return None

    def insert_id(self, sname, skind, skinds, stype):
        """Inserts new identifier at the end of symbol table, if possible.
           Returns symbol index, or raises exception if symbol alredy exists
           sname   - symbol name
           skind   - symbol kind
           skinds  - symbol kinds to check for
           stype   - symbol type
           loc     - location (character position) of text being parsed
           text    - text being parsed
        """
        index = self.lookup_symbol(sname, skinds)
        if index == None:
            index = self.insert_symbol(sname, skind, stype)
            return index
        else:
            raise SemanticException("Redefinition of %s" % sname, self.compiler.loc, self.compiler.text)

    def insert_global_var(self, vname, vtype):
        "Inserts new global variable"
        return self.insert_id(vname, self.kinds.GLOBAL_VAR, [self.kinds.GLOBAL_VAR, self.kinds.FUNCTION], vtype)

    def insert_local_var(self, vname, vtype):
        "Inserts new local variable"
        return self.insert_id(vname, self.kinds.LOCAL_VAR, [self.kinds.LOCAL_VAR, self.kinds.PARAMETER], vtype)

    def insert_parameter(self, pname, ptype):
        "Inserts new parameter"
        index = self.insert_id(pname, self.kinds.PARAMETER, self.kinds.PARAMETER, ptype)
        self.table[index].set_attribute("Index", self.compiler.function_params)
        self.table[self.compiler.function_index].param_types.append(ptype)
        return index

    def insert_function(self, fname, ftype):
        "Inserts new function"
        index = self.insert_id(fname, self.kinds.FUNCTION, [self.kinds.GLOBAL_VAR, self.kinds.FUNCTION], ftype)
        self.table[index].set_attribute("Params",0)
        return index

    def insert_constant(self, cname, ctype):
        """Inserts constant (or returns index if constant already exists)"""
        index = self.lookup_symbol(cname, stype=ctype)
        if index == None:
            num = int(cname)
            if ctype == self.types.INT:
                if (num < CodeGenerator.MIN_INT) or (num > CodeGenerator.MAX_INT):
                    raise SemanticException("Integer constant %s out of range" % cname, self.compiler.loc, self.compiler.text)
            elif ctype == self.types.UNSIGNED:
                if (num < 0) or (num > CodeGenerator.MAX_UNSIGNED):
                    raise SemanticException("Unsigned constant %s out of range" % cname, self.compiler.loc, self.compiler.text)
            index = self.insert_symbol(cname, self.kinds.CONSTANT, ctype)
        return index

    def same_types(self, index1, index2):
        return self.table[index1].type == self.table[index2].type != self.types.NO_TYPE
    
    def same_argument_types(self, function, index, argument_number):
        return self.table[function].param_types[argument_number] == self.table[index].type

    def get_attribute(self, index):
        return self.table[index].attribute

    def set_attribute(self, index, value):
        self.table[index].attribute = value

    def get_name(self, index):
        return self.table[index].name

    def get_kind(self, index):
        return self.table[index].kind

    def get_type(self, index):
        return self.table[index].type
    def set_type(self, index, stype):
        self.table[index].type = stype

#############################################################################################################################
#############################################################################################################################

class CodeGenerator(object):
    """Class for code generation methods."""

    #bit size of variables
    TYPE_BIT_SIZE = 16
    #min/max values of constants
    MIN_INT = -2 ** (TYPE_BIT_SIZE - 1)
    MAX_INT = 2 ** (TYPE_BIT_SIZE - 1) - 1
    MAX_UNSIGNED = 2 ** TYPE_BIT_SIZE - 1
    #available working registers (the last one is register for function's return value!)
    registers = "%0 %1 %2 %3 %4 %5 %6 %7 %8 %9 %10 %11 %12 %13".split()
    #register for function's return value
    FUNCTION_REGISTER = len(registers) - 1
    #index of last working register
    LAST_WORKING_REGISTER = len(registers) - 2

    def __init__(self):
        self.code = ""
        self.internal = "@"
        self.definition = ":"
        #self.free_reg_number = 0
        #self.free_registers = dict([i,reg] for i, reg in enumerate(self.registers))
        self.free_registers = range(self.FUNCTION_REGISTER, -1, -1)
        self.used_registers = []
        self.compiler = None
        self.symtab = None
        self.operations = {"+" : "ADD", "-" : "SUB", "*" : "MUL", "/" : "DIV"}
        self.opsigns = {SymbolTable.types.NO_TYPE : "U", SymbolTable.types.INT : "S", SymbolTable.types.UNSIGNED : "U"}
        self.used_registers_stack = []

    def error(self, text):
        """This exeption is not handled by parser, to allow traceback printing"""
        raise Exception("Compiler error: %s" % text)

#    def take_register(self, rtype = SymbolTable.types.NO_TYPE):
#        if self.free_reg_number > self.LAST_WORKING_REGISTER:
#            self.error("no more free registers")
#        reg = self.free_reg_number
#        self.symtab.set_type(reg, rtype)
#        self.free_reg_number += 1
#        return reg

#    def free_register(self, reg = None):
#        if (reg != None) and ((reg < 0) or (reg > self.LAST_WORKING_REGISTER)):
#            return
#        if self.free_reg_number == 0:
#            self.error("no more registers to free")
#        self.symtab.set_type(self.free_reg_number, SymbolTable.types.NO_TYPE)
#        self.free_reg_number -= 1

    def take_register(self, rtype = SymbolTable.types.NO_TYPE):
        """Reserves one working register and sets its type"""
        if len(self.free_registers) == 0:
            self.error("no more free registers")
        reg = self.free_registers.pop()
        self.used_registers.append(reg)
        self.symtab.set_type(reg, rtype)
        return reg

    def take_function_register(self, rtype = SymbolTable.types.NO_TYPE):
        """Reserves register for function return value"""
        reg = self.FUNCTION_REGISTER
        if reg not in self.free_registers:
            self.error("function register already taken")
        self.free_registers.remove(reg)
        self.used_registers.append(reg)
        self.symtab.set_type(reg, rtype)
        return reg

    def free_register(self, reg):
        """Releases working register"""
        if reg not in self.used_registers:
            self.error("register %s is not taken" % self.registers[reg])
        self.used_registers.remove(reg)
        self.free_registers.append(reg)
        self.free_registers.sort(reverse = True)

    def free_if_register(self, index):
        """If index is working register, free it, otherwise just return (helper function)"""
        if (index < 0) or (index > self.FUNCTION_REGISTER):
            return
        else:
            self.free_register(index)

    def label(self, name, internal=False, definition=False):
        """Generates label name
           name - label name
           internal - boolean value, adds "@" prefix to label
           definition - boolean value, adds ":" suffix to label
        """
        return "{0}{1}{2}".format(self.internal if internal else "", name, self.definition if definition else "")

    def symbol(self, index):
        """Generates symbol name from index"""
        if isinstance(index, str):
            return index
        if (index < 0) or (index >= self.symtab.table_len):
            self.error("symbol table index out of range")
        sym = self.symtab.table[index]
        if sym.kind == SymbolTable.kinds.LOCAL_VAR:
            return "-{0}(%14)".format(sym.attribute * 4)
        elif sym.kind == SymbolTable.kinds.PARAMETER:
            return "{0}(%14)".format(4 + sym.attribute * 4)
        elif sym.kind == SymbolTable.kinds.CONSTANT:
            return "${0}".format(sym.name)
        else:
            return "{0}".format(sym.name)

    def save_used_registers(self):
        """Pushes all used working registers before function call"""
        used = self.used_registers[:]
        del self.used_registers[:]
        self.used_registers_stack.append(used[:])
        used.sort()
        for reg in used:
            self.newline_text("PUSH\t%s" % self.registers[reg], True)

    def restore_used_registers(self):
        """Pops all used working registers after function call"""
        used = self.used_registers_stack.pop()
        self.used_registers = used[:]
        used.sort(reverse = True)
        for reg in used:
            self.newline_text("POP \t%s" % self.registers[reg], True)

    def text(self, text):
        """Inserts text into generated code"""
        self.code += text

    def newline(self, indent=False):
        """Inserts newline, optionally with indentation."""
        self.text("\n")
        if indent:
            self.text("\t\t")

    def newline_text(self, text, indent = False):
        """Inserts newline and text, optionally with indentation (helper function)"""
        self.newline(indent)
        self.text(text)

    def newline_label(self, name, internal=False, definition=False):
        """Inserts newline and label (helper function)
           name - label name
           internal - boolean value, adds "@" prefix to label
           definition - boolean value, adds ":" suffix to label
        """
        self.newline_text(self.label("{0}{1}{2}".format("@" if internal else "", name, ":" if definition else "")))

    def global_var(self, name):
        """Inserts new global variable definition"""
        self.newline_label(name, False, True)
        self.newline_text("WORD\t1", True)

    def function_begin(self):
        """Inserts function name label with function frame initialization"""
        self.newline_label(self.compiler.function_name, False, True)
        self.push("%14")
        self.move("%15", "%14")

    def function_middle(self):
        """Inserts local variable initialization with body label"""
        if self.compiler.function_vars > 0:
            #self.newline_text("SUBU \t%%15, $%d, %%15" % (self.compiler.function_vars * 4), True)
            print self.compiler.function_vars
            const = self.symtab.insert_constant("{0}".format(self.compiler.function_vars * 4), SymbolTable.types.UNSIGNED)
            self.arithmetic("%15","-",const,"%15")
        self.newline_label(self.compiler.function_name+"_body", True, True)

    def function_end(self):
        """Inserts function return with exit label"""
        self.newline_label(self.compiler.function_name+"_exit", True, True)
        #self.newline_text("MOV \t%14, %15", True)
        self.move("%14", "%15")
        #self.newline_text("POP \t%14", True)
        self.pop("%14")
        self.newline_text("RET", True)

    def arithmetic_mnemonic(self, op_name, op_type):
        """Generates arithmetic operation mnemonic"""
        return self.operations[op_name] + self.opsigns[op_type]

    def arithmetic(self,operand1, operator, operand2, operand3 = None):
        """Generates arithmetic operation"""
        if isinstance(operand1, int):
            typ = self.symtab.get_type(operand1)
            self.free_if_register(operand1)
        else:
            typ = None
        if isinstance(operand2, int):
            typ = self.symtab.get_type(operand2) if typ == None else typ
            self.free_if_register(operand2)
        else:
            typ = SymbolTable.types.NO_TYPE if typ == None else typ
        if operand3 == None:
            reg = self.take_register(typ)
        else:
            reg = operand3
        mne = self.arithmetic_mnemonic(operator, typ)
        self.newline_text("{0}\t{1}, {2}, {3}".format(mne, self.symbol(operand1), self.symbol(operand2), self.symbol(reg)), True)
        return reg

    def move(self,operand1, operand2):
        """Generates move operation"""
        if isinstance(operand1, int):
            typ = self.symtab.get_type(operand1)
            self.free_if_register(operand1)
        else:
            typ = SymbolTable.types.NO_TYPE
        self.newline_text("MOV \t{0}, {1}".format(self.symbol(operand1), self.symbol(operand2)), True)
        if isinstance(operand2, int):
            if self.symtab.get_kind(operand2) == SymbolTable.kinds.WORKING_REGISTER:
                self.symtab.set_type(operand2, typ)

    def jump(self,jump, label):
        """Generates jump operation"""
        self.newline_text("{0}\t{1}".format(jump, label), True)

    def push(self, operand):
        """Generates push operation"""
        self.newline_text("PUSH\t%s" % self.symbol(operand), True)

    def pop(self, operand):
        """Generates pop operation"""
        self.newline_text("POP \t%s" % self.symbol(operand), True)

    def function_call(self, function, arguments):
        for arg in arguments:
            self.push(self.symbol(arg))
        self.newline_text("CALL\t"+self.symtab.get_name(function), True)
        args = self.symtab.get_attribute(function)
        if args > 0:
            args_space = self.symtab.insert_constant("{0}".format(args * 4), SymbolTable.types.UNSIGNED)
            self.arithmetic("%15", "-", args_space, "%15")


#############################################################################################################################
#############################################################################################################################

class MicroC(object):
    """Class for microC parser"""

    def __init__(self):
        self.tId = Word(alphas+"_",alphanums+"_")
        self.tInteger = Word(nums).setParseAction(lambda x : [x[0], SymbolTable.types.INT])
        self.tUnsigned = Regex(r"[0-9]+[uU]").setParseAction(lambda x : [x[0][:-1], SymbolTable.types.UNSIGNED])
        self.tConstant = (self.tUnsigned | self.tInteger).setParseAction(self.constant_action)
        self.tType = Keyword("int").setParseAction(lambda x : SymbolTable.types.INT) | \
                     Keyword("unsigned").setParseAction(lambda x : SymbolTable.types.UNSIGNED)
        self.tRelOp = oneOf("< > <= >= == !=")
        self.tMulOp = oneOf("* /")
        self.tAddOp = oneOf("+ -")

        self.rGlobalVariable = (self.tType("type") + self.tId("name") + FollowedBy(";")).setParseAction(self.global_variable_action)
        self.rGlobalVariableList = Group(ZeroOrMore(self.rGlobalVariable + Suppress(";")))

        self.rExp = Forward()
        self.rMulExp = Forward()
        self.rNumExp = Forward()
        self.rArguments = Optional(self.rNumExp("exp").setParseAction(self.argument_action) +
                                   ZeroOrMore(Suppress(",") + self.rNumExp("exp").setParseAction(self.argument_action)))
        self.rFunctionCall = ((self.tId("name") + FollowedBy("(")).setParseAction(self.function_call_prepare_action) +
                              Suppress("(") + self.rArguments("args") + Suppress(")")).setParseAction(self.function_call_action)
        self.rExp << (self.rFunctionCall("function") | self.tConstant("const") | 
                      self.tId("name").setParseAction(self.find_var_action) |
                      Group(Suppress("(") + self.rNumExp + Suppress(")"))("parenexp") |
                      Group("+" + self.rExp)("plusexp") | Group("-" + self.rExp)("minusexp")).setParseAction(lambda x : x[0])
        self.rMulExp << ((self.rExp("mulexp") + ZeroOrMore(self.tMulOp + self.rExp))).setParseAction(self.mulexp_action)
        self.rNumExp << (self.rMulExp + ZeroOrMore(self.tAddOp + self.rMulExp)).setParseAction(self.numexp_action)

        self.rAndExp = Forward()
        self.rLogExp = Forward()
        self.rRelExp = Group(self.rNumExp + self.tRelOp + self.rNumExp)
        self.rAndExp << (self.rRelExp | Group(self.rAndExp + "&&" + self.rRelExp))
        self.rLogExp << (self.rAndExp | Group(self.rLogExp + "||" + self.rAndExp))

        self.rStatement = Forward()
        self.rStatementList = Forward()
        self.rReturnStatement = (Keyword("return") + self.rNumExp("exp") + Suppress(";")).setParseAction(self.function_return_action)
        self.rAssignmentStatement = (self.tId("var") + Literal("=") + self.rNumExp("exp") + Suppress(";")).setParseAction(self.assignment_action)
        self.rFunctionCallStatement = self.rFunctionCall + Suppress(";")
        self.rIfStatement = Group(Keyword("if") + Suppress("(") + self.rLogExp + Suppress(")") +
                                  self.rStatement + Optional(Keyword("else") + self.rStatement))
        self.rWhileStatement = Group(Keyword("while") + Suppress("(") + self.rLogExp + Suppress(")") + self.rStatement)
        self.rCompoundStatement = Group("{" + self.rStatementList + "}")
        self.rStatement << (self.rAssignmentStatement | self.rReturnStatement | self.rFunctionCallStatement |
                            self.rIfStatement | self.rWhileStatement | self.rCompoundStatement)
        self.rStatementList << ZeroOrMore(self.rStatement)

        self.rLocalVariable = (self.tType("type") + self.tId("name") + FollowedBy(";")).setParseAction(self.local_variable_action)
        self.rLocalVariableList = Group(ZeroOrMore(self.rLocalVariable + Suppress(";")))
        self.rBody = Literal("{") + Optional(self.rLocalVariableList).setParseAction(self.function_body_action) + self.rStatementList + Literal("}")
        self.rParameter = (self.tType("type") + self.tId("name")).setParseAction(self.parameter_action)
        self.rParameterList = Optional(self.rParameter + ZeroOrMore(Suppress(",") + self.rParameter))
        self.rFunction = ((self.tType("type") + self.tId("name")).setParseAction(self.function_begin_action) +
                          Group(Literal("(") + self.rParameterList("params") + Literal(")") + self.rBody)).setParseAction(self.function_end_action)
        self.rFunctionList = Group(self.rFunction + ZeroOrMore(self.rFunction))

        self.rProgram = (self.rGlobalVariableList + self.rFunctionList)

        self.symtab = SymbolTable()
        self.codegen = CodeGenerator()

        self.compiler = SharedData()
        self.symtab.compiler = self.compiler
        self.codegen.compiler = self.compiler
        self.codegen.symtab = self.symtab

        self.function_call_index = -1
        self.function_call_stack = []
        self.function_arguments = []
        self.function_arguments_stack = []
        self.function_arguments_number = -1
        self.function_arguments_number_stack = []

    def global_variable_action(self, text, loc, var):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "GLOBAL_VAR:",var
            if DEBUG > 9: return
        index = self.symtab.insert_global_var(var.name, var.type)
        self.codegen.global_var(var.name)
        return index

    def local_variable_action(self, text, loc, var):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "LOCAL_VAR:",var
            if DEBUG > 9: return
        index = self.symtab.insert_local_var(var.name, var.type)
        self.compiler.function_vars += 1
        return index

    def parameter_action(self, text, loc, par):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "PARAM:",par
            if DEBUG > 9: return
        index = self.symtab.insert_parameter(par.name, par.type)
        self.compiler.function_params += 1
        return index

    def constant_action(self, text, loc, const):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "CONST:",const
            if DEBUG > 9: return
        return self.symtab.insert_constant(const[0], const[1])

    def function_begin_action(self, text, loc, fun):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "FUN_BEGIN:",fun
            if DEBUG > 9: return
        self.compiler.function_index = self.symtab.insert_function(fun.name, fun.type)
        self.compiler.function_name = fun.name
        self.compiler.function_params = 0
        self.compiler.function_vars = 0
        self.codegen.function_begin();

    def function_body_action(self, text, loc, fun):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "FUN_BODY:",fun
            if DEBUG > 9: return
        self.codegen.function_middle()

    def function_end_action(self, text, loc, fun):
        if DEBUG > 0:
            print "FUN_END:",fun
            if DEBUG > 9: return
        self.symtab.set_attribute(self.compiler.function_index, self.compiler.function_params)
        self.symtab.clear_symbols(self.compiler.function_index+1)
        self.codegen.function_end()

    def function_return_action(self, text, loc, ret):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "RETURN:",ret
            if DEBUG > 9: return
        if not self.symtab.same_types(self.compiler.function_index, ret.exp[0]):
            raise SemanticException("Incompatible type in return", loc, text)
        self.codegen.move(ret.exp[0], self.codegen.FUNCTION_REGISTER)
        self.codegen.jump("JMP ", self.codegen.label(self.compiler.function_name+"_exit", True))

    def find_var_action(self, text, loc, var):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "EXP_VAR:",var
            if DEBUG > 9: return
        var_index = self.symtab.lookup_symbol(var.name, [SymbolTable.kinds.GLOBAL_VAR, SymbolTable.kinds.PARAMETER, SymbolTable.kinds.LOCAL_VAR])
        if var_index == None:
            raise SemanticException("%s undefined" % var.name, loc, text)
        return var_index

    def assignment_action(self, text, loc, assign):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "ASSIGN:",assign
            if DEBUG > 9: return
        var_index = self.symtab.lookup_symbol(assign.var, [SymbolTable.kinds.GLOBAL_VAR, SymbolTable.kinds.PARAMETER, SymbolTable.kinds.LOCAL_VAR])
        if var_index == None:
            raise SemanticException("Invalid lvalue %s in assignment" % assign.var, loc, text)
        if not self.symtab.same_types(var_index, assign.exp[0]):
            raise SemanticException("Incompatible types in assignment", loc, text)
        self.codegen.move(assign.exp[0], var_index)

    def exp_action(self, text, loc, exp):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "EXP:",exp
            if DEBUG > 9: return
        return exp[0]

    def mulexp_action(self, text, loc, mul):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "MUL_EXP:",mul
            if DEBUG > 9: return
        m = list(mul)
        while len(m) > 1:
            if not self.symtab.same_types(m[0], m[2]):
                raise SemanticException("Invalid opernads to binary %s" % m[1], loc, text)
            reg = self.codegen.arithmetic(*m[0:3])
            m[0:3] = [reg]
        return m[0]

    def numexp_action(self, text, loc, num):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "NUM_EXP:",num
            if DEBUG > 9: return
        #print "NUM:",num
        n = list(num)
        while len(n) > 1:
            if not self.symtab.same_types(n[0], n[2]):
                raise SemanticException("Invalid opernads to binary %s" % n[1], loc, text)
            reg = self.codegen.arithmetic(*n[0:3])
            n[0:3] = [reg]
        return n[0]

    """
function_call
    :   _ID
            {
                int index;
                if( (index = lookup_symbol((char *)$1, FUNCTION)) == -1 ) {
                    sprintf(char_buffer, "'%s' is not a function", (char *)$1);
                    yyerror(char_buffer);
                }
                push(&function_call_stack, function_call_index);
                function_call_index = index;
                gen_reg_save();
            }
        _LPAREN arguments _RPAREN
            {
                check_arguments_number(function_call_index, arg_num);
                
                gen_function_call(function_call_index);
                gen_clear_loc_var(arg_num);
                
                arg_num = pop(&argument_number_stack);
                
                //postavi tip povratne vrednosti funkcije u %13
                set_register_type(FUNCTION_REGISTER, 
                                  get_type(function_call_index));
                function_call_index = pop(&function_call_stack);
                gen_reg_restore();
                
                //povratna vrednost funkcije se uvek nalazi u %13
                $$ = FUNCTION_REGISTER;
            }
    ;"""


    def function_call_prepare_action(self, text, loc, fun):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "FUN_PREP:",fun
            if DEBUG > 5: return
        index = self.symtab.lookup_symbol(fun.name, SymbolTable.kinds.FUNCTION)
        if index == None:
            raise SemanticException("'%s' is not a function" % fun.name, loc, text)
        self.function_call_stack.append(self.function_call_index)
        self.function_call_index = index
        self.function_arguments_stack.append(self.function_arguments[:])
        del self.function_arguments[:]
        self.codegen.save_used_registers()

    def argument_action(self, text, loc, arg):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "ARG:",arg
            if DEBUG > 5: return
        if not self.symtab.same_argument_types(self.function_call_index, arg.exp, len(self.function_arguments)):
            raise SemanticException("Incompatible type for argument %d in '%s'" % (len(self.function_arguments) + 1, self.symtab.get_name(self.function_call_index)), loc, text)
        self.function_arguments.append(arg.exp)

    def function_call_action(self, text, loc, fun):
        self.compiler.setpos(loc,text)
        if DEBUG > 0:
            print "FUNC:",fun
            self.symtab.display()
            #if DEBUG > 5: return self.codegen.take_function_register(1)
            if DEBUG > 5: return

        if len(self.function_arguments) != self.symtab.get_attribute(self.function_call_index):
            raise SemanticException("Wrong number of arguments to function '%s'" % fun.name, loc, text)
        self.function_arguments.reverse()
        self.codegen.function_call(self.function_call_index, self.function_arguments)
        self.codegen.restore_used_registers()
        return_type = self.symtab.get_type(self.function_call_index)
        self.function_call_index = self.function_call_stack.pop()
        self.function_arguments = self.function_arguments_stack.pop()
        return self.codegen.take_function_register(return_type)

    def parse(self,text):
        try:
            return self.rProgram.parseString(text, parseAll=True)
        except SemanticException, err:
            print err
        except ParseException, err:
            print err

#############################################################################################################################
#############################################################################################################################

mc = MicroC()

test1 = """    int a;
    int b;
    int c;
    unsigned d;

    int fun(int z) {
        return 123;
    }

    int fun2(int z, unsigned w) {
        unsigned r;
        unsigned t;
        return 1234;
    }

    int main(int x, int y) {
        int w;
        unsigned z;
        b = fun(3);
        b = fun2(b,d);
    }
"""
test2 = """    int a;

        a = a + 1;
        b = b * 2;
        c = c * a + b;
        return a + 4555;

    int b;
    int c;
    unsigned d;

    int fun(int z) {
        return 123;
    }

    int main(int x, int y) {
        int w;
        unsigned z;
        a = fun(2,3*4/5);
        if (a<2) a = a + 1;
        else b = b * 2;
        while (c<a) c = c *a+b;
        return a+45555u;
    }
"""

mc.parse(test1)
print mc.codegen.code
mc.symtab.display()

print mc.codegen.free_registers

#print mc.rFunctionCall.parseString(test2,parseAll=True)
#print mc.rNumExp.parseString(test2,parseAll=True)
#print mc.tConstant.parseString(test2,parseAll=True)

