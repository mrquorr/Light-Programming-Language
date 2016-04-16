import light_scanner as lexer
import ply.yacc as yacc
from light_semantic_controller import *
from quadruple import *

tokens = lexer.tokens
function_stack = Stack()
tmp_var = Var()

tmp_function = Function()
function_stack.push('program')

#TODO: Chech what data structure is the best for this case
function_queue = Queue()

#Default functions in queue
function_queue.enqueue('program')
function_queue.enqueue('window_size')
function_queue.enqueue('coordinates')

# Quads global structures
operand_stack   = Stack()
operator_stack  = Stack()
type_stack      = Stack()

# Global track keeping
constant_dict = {}
last_func_called = ""
param_counter = 0

# Conditions
#NO SE NECESITA
missing_return_stmt = False

# Helper Functions
def build_and_push_quad(op, l_op, r_op, res):
	tmp_quad = Quadruple()
	tmp_quad.build(op, l_op, r_op, res)
	Quadruples.push_quad(tmp_quad)

def exp_quad_helper(p, op_list):
	if operator_stack.isEmpty():
		return
	op = operator_stack.peek()
	str_op = inv_op_dict[op]
	if str_op in op_list:
		t1 = type_stack.pop()
		t2 = type_stack.pop()
		return_type = SemanticCube.cube[op][t1][t2]
		if return_type == -1:
			Error.type_mismatch(p.lexer.lineno, t1, t2, str_op)
		o1 = operand_stack.pop()
		o2 = operand_stack.pop()
		tmp_var_id = SemanticInfo.get_next_var_id(return_type)

		# Generate Quadruple and push it to the list
		build_and_push_quad(op, o2, o1, tmp_var_id)
		operator_stack.pop()

		# push the tmp_var_id and the return type to stack
		operand_stack.push(tmp_var_id)
		type_stack.push(return_type)

def assign_quad_helper():
	t1 = type_stack.pop()
	t2 = type_stack.pop()
	if t1 != t2:
		Error.type_mismatch(p.lexer.lineno, t1, t2, '=')
	op = operator_stack.pop()
	o1 = operand_stack.pop()
	o2 = operand_stack.pop()

	# Generate Quadruple and push it to the list
	build_and_push_quad(op, o1, None, o2)


def print_quad_helper():
	operand = operand_stack.pop()
	op = operator_stack.pop()
	build_and_push_quad(op, None, None, operand)
	type_stack.pop()

def push_const_operand_and_type(operand, type):
	type_stack.push(type_dict[type])
	if operand in constant_dict.keys():
		operand_stack.push(constant_dict[operand])
		return
	addr = SemanticInfo.get_next_const_id()
	operand_stack.push(addr)
	constant_dict[operand] = addr

def print_stacks():
	sys.stdout.write("> Operand Stack = ")
	operand_stack.pprint()

	sys.stdout.write("> Operator Stack = ")
	operator_stack.pprint()

	sys.stdout.write("> Type Stack = ")
	type_stack.pprint()

# STATEMENTS ###################################################################
# http://snatverk.blogspot.mx/2011/01/parser-de-mini-c-en-python.html

def p_program (p):
	'''
	program  : PROGRAM VAR_IDENTIFIER SEP_LCBRACKET pr_a pr_b main_func SEP_RCBRACKET
	'''
	function_stack.pop()
	SemanticInfo.reset_var_ids()
	FunctionTable.print_all()
	sys.stdout.write("Constants dict: ")
	print constant_dict
	Quadruples.print_all()
	

def p_pr_a (p):
	'''
	pr_a  : vars pr_a 
		| epsilon
	'''

def p_pr_b (p):
	'''
	pr_b  : function pr_b 
		| epsilon
	'''

def p_main_func (p):
	'''
	main_func : LIGHT_TOKEN new_func_scope SEP_LPAR SEP_RPAR SEP_LCBRACKET pr_a stmt_loop SEP_RCBRACKET
	'''
	function_stack.pop()
	SemanticInfo.reset_var_ids()
	# Generates the 'END' action to finish execution
	build_and_push_quad(special_operator_dict['end'], None, None, None)
	# TODO: Liberar tabla de variables

def p_type (p):
	'''
	type : primitive_type 
		| figure 
		| epsilon
	'''
	p[0] = p[1]

def p_primitive_type (p):
	'''
	primitive_type : BOOLEAN 
				| INT 
				| DECIMAL 
				| STRING 
	'''
	p[0] = p[1]
	tmp_var.type = type_dict[p[1]]
	tmp_function.type = type_dict[p[1]]

def p_figure (p):
	'''
	figure : POINT 
			| LINE 
			| TRIANGLE 
			| SQUARE 
			| RECTANGLE 
			| POLYGON 
			| STAR 
			| CIRCLE
	'''
	p[0] = p[1]

def p_stmt_loop (p):
	'''
	stmt_loop : statement  stmt_loop
		| epsilon
	'''

def p_function (p):
	'''
	function : FUNCTION VAR_IDENTIFIER new_func_scope SEP_LPAR func_a SEP_RPAR func_b SEP_LCBRACKET func_c stmt_loop tmp_return verify_return_stmt SEP_RCBRACKET
	'''
	function_stack.pop()
	SemanticInfo.reset_var_ids()
	# Generates the 'RET' action at the end of the function
	build_and_push_quad(special_operator_dict['ret'], None, None, None)
	missing_return_stmt = False # resetting var
	# TODO: Liberar tabla de variables

def p_func_a (p):
	'''
	func_a : parameters
		| epsilon
	'''
def p_func_b (p):
	'''
	func_b : RETURNS add_return_val primitive_type
		| epsilon
	'''

def p_add_return_val (p):
	'''
	add_return_val : epsilon
	'''
	if (p[-1] == "returns"):
		missing_return_stmt = True

	FunctionTable.add_return_type_to_func(tmp_function.name, tmp_function.type)

def p_func_c (p):
	'''
	func_c : vars func_c
		| epsilon
	'''

def p_tmp_return(p):
	'''
	tmp_return : RETURN opt_exp
		| epsilon
	'''

def p_opt_exp(p):
	'''
	opt_exp : exp return_found 
		| epsilon
	'''

def p_return_found(p):
	'''
	return_found : epsilon 
	'''
	#if function is void and has return
	if FunctionTable.function_returns_void(function_stack.peek()):
		Error.return_type_function_void(function_stack.peek(), p.lexer.lineno)

	#found Return Type
	FunctionTable.set_return_found(function_stack.peek(), True)

def p_verify_return_stmt(p):
	'''
	verify_return_stmt : 
	'''
	#if function is not void
	if not FunctionTable.function_returns_void(function_stack.peek()):
		if not FunctionTable.function_has_return_stmt(function_stack.peek()):
			Error.no_return_type(function_stack.peek(), p.lexer.lineno)


def p_new_func_scope(p):
	'new_func_scope :'
	function_stack.push(p[-1])
	function_queue.enqueue(p[-1])
	tmp_function.name = p[-1]
	tmp_function.type = type_dict['void']
	tmp_function.quad_index = Quadruples.next_free_quad
	FunctionTable.add_function(tmp_function)

def p_parameters (p):
	'parameters : VAR_IDENTIFIER SEP_COLON type new_param_seen param_a'

def p_new_param_seen(p):
	'new_param_seen : '
	tmp_var.name = p[-3]
	tmp_var.type = type_dict[p[-1]]
	FunctionTable.add_var_to_func(tmp_function.name, tmp_var)
	FunctionTable.add_param_to_func(tmp_function.name, p[-3], tmp_var.type)

def p_param_a (p):
	'''
	param_a : SEP_COMMA parameters
		| epsilon
	'''

def p_function_call(p):
	'''
	function_call : VAR_IDENTIFIER verify_function_call test SEP_LPAR call_parameters SEP_RPAR
	'''
	func = FunctionTable.function_dict[p[1]]
	address = func.quad_index
	build_and_push_quad(special_operator_dict['gosub'], p[1], None, address)

	# verify arguments count
	global param_counter
	n = len(func.params)
	if param_counter != n:
		Error.param_number_mismatch(p.lexer.lineno-1, p[1], n, param_counter)

	param_counter = 0 # global var reset

def p_verify_function_call(p):
	'verify_function_call : epsilon'
	# print("Function queue")
	# TODO: delegate this task to FunctionTable class
	if not function_queue.inQueue(p[-1]):
		Error.function_not_defined(p[-1],p.lexer.lineno)
	global last_func_called
	last_func_called = p[-1]
	func = FunctionTable.function_dict[p[-1]]
	build_and_push_quad(special_operator_dict['era'], func.name, None, None)


def p_test(p):
	'''
	test : 
	'''
	print("test: " + str(p.lexer.lineno))

def p_call_parameters(p):
	'''
	call_parameters : VAR_IDENTIFIER SEP_COLON exp verify_param call_param_a
		| epsilon
	'''
def p_call_param_a(p):
	'''
	call_param_a : SEP_COMMA call_parameters
		| epsilon
	'''
def p_verify_param(p):
	'verify_param : '
	param_name = p[-3]
	arg = operand_stack.pop()
	arg_type = type_stack.pop()
	if not FunctionTable.verify_param_at_index(last_func_called, param_name, arg_type, param_counter):
		Error.param_mismatch( p.lexer.lineno, param_name, arg_type)
	build_and_push_quad(special_operator_dict['param'], arg, None, param_counter)
	global param_counter
	param_counter = param_counter + 1
 
def p_assignment (p):
	'''
	assignment : var_id OP_EQUALS push_operator assgn_a 
	'''
	print("assignment: " + str(p.lexer.lineno))
	assign_quad_helper()


def p_assgn_a(p):
	'''
	assgn_a : exp
		| function_call
	'''
	print("ASSIGN A: " + str(p.lexer.lineno))

def p_cycle (p):
	'''
	cycle : while 
		| for_each do_block
		| for 
	'''
	print("cycle: " + str(p.lexer.lineno))

def p_while (p):
	'''
	while : WHILE SEP_LPAR condition SEP_RPAR start_loop_helper do_block end_while_helper
	'''

def p_end_while_helper (p) :
	'''
	end_while_helper : epsilon
	'''
	tmp_false = Quadruples.pop_jump()
	tmp_return = Quadruples.pop_jump()

	#fill the return value
	build_and_push_quad(17, None, None, tmp_return - 1)


	#fill false with count
	tmp_count = Quadruples.next_free_quad
	tmp_quad = Quadruples.fill_missing_quad(tmp_false, tmp_count)


# def p_l_a (p):
# 	'''
# 	l_a : VAR_INT
# 		| VAR_IDENTIFIER verify_variable
# 	'''

def p_for_each (p):
	'''
	for_each : FOR_EACH SEP_LPAR VAR_IDENTIFIER IN for_each_collection SEP_RPAR
	'''
def p_for_each_collection(p):
	'''
	for_each_collection : VAR_IDENTIFIER
		| SEP_LBRACKET VAR_INT SEP_DOT SEP_DOT VAR_INT SEP_RBRACKET
	'''

def p_for (p):
	'''
	for : FOR SEP_LPAR for_a SEP_SEMICOLON condition start_loop_helper SEP_SEMICOLON for_b SEP_RPAR do_block end_for_helper
	'''
	print("for" + str(p.lexer.lineno))

def p_start_loop_helper (p):
	'''
	start_loop_helper : epsilon
	'''

	#Put count in JUMPSTACK
	Quadruples.push_jump(0)

	aux = type_stack.pop()
	if aux != 1 :
		Error.not_a_condition(aux, p.lexer.lineno)
	else :
		res = operand_stack.pop()
		operator = special_operator_dict['gotof']

		# Generate Quadruple and push it to the list
		tmp_quad = Quadruple()
		tmp_quad.build(operator, res, None, None)
		Quadruples.push_quad(tmp_quad)

		#Push into jump stack
		Quadruples.push_jump(-1)

def p_end_for_helper (p) :
	'''
	end_for_helper : epsilon
	'''
	tmp_false = Quadruples.pop_jump()
	tmp_return = Quadruples.pop_jump()

	offset = p[-3]
	#fill the return value
	build_and_push_quad(17, None, None, tmp_return - offset)


	#fill false with count
	tmp_count = Quadruples.next_free_quad
	tmp_quad = Quadruples.fill_missing_quad(tmp_false, tmp_count)


def p_for_a (p):
	'''
	for_a : assignment 
		| epsilon
	'''


# def p_for_assignment (p) :
# 	'''
# 	for_assignment : VAR_IDENTIFIER verify_variable OP_EQUALS for_var_cte
# 	'''

def p_for_b (p):
	'''
	for_b : increment tmp_increment
		| assignment tmp_assign
	'''
	p[0] = p[2]

def p_tmp_increment (p):
	'tmp_increment : epsilon'
	p[0] = 1

def p_tmp_assign (p):
	'tmp_assign : epsilon'
	p[0] = 0

# def p_for_increment (p):
# 	'''
# 	for_increment : VAR_IDENTIFIER verify_variable inc_a for_var_cte
# 	'''
# 	#push_operator


# def p_for_var_cte(p): 
# 	'''
# 	for_var_cte : VAR_IDENTIFIER verify_variable
# 		| VAR_INT
# 		| VAR_DECIMAL
# 	'''

def p_action (p):
	'''
	action : ACTION act_a 
	'''

def p_act_a (p):
	'''
	act_a : act_move
		| act_scale
		| act_visible
		| act_rotate
	'''

def p_act_header (p):
	'''
	act_header : VAR_IDENTIFIER DO  BEGINS SEP_COLON exp SEP_COMMA  ENDS SEP_COLON exp 
	'''

def p_act_move (p):
	'''
	act_move : MOVE act_header SEP_COMMA POS_X SEP_COLON exp SEP_COMMA  POS_Y SEP_COLON exp  END
	'''

def p_act_scale (p):
	'''
	act_scale : SCALE act_header SEP_COMMA SIZE SEP_COLON exp END
	'''

def p_act_rotate (p):
	'''
	act_rotate : SCALE act_header SEP_COMMA ANGLE SEP_COLON exp SEP_COMMA  END
	'''

def p_act_visible (p):
	'''
	act_visible : HIDE act_header END
		| SHOW act_header END
	'''

def p_camera (p):
	'''
	camera : CAMERA VAR_IDENTIFIER 
	'''


##AND OR ret
def p_condition (p):
	'''
	condition : expresion quad_helper_and_or cond_a
	'''
	print("condition: " + str(p.lexer.lineno))

def p_cond_a(p):
	'''
	cond_a : oper_a condition
		| epsilon
	'''

def p_oper_a(p):
	'''
	oper_a : AND
		| OR
	'''
	operator_stack.push(operator_dict[p[1]])

def p_quad_helper_and_or(p):
	'quad_helper_and_or : '
	exp_quad_helper(p, ['and', 'or'])

def p_expresion(p):
	'''
	expresion : exp quad_helper_cond expresion_a
	'''
	print("expresion: " + str(p.lexer.lineno))

def p_expresion_a(p):
	'''
	expresion_a : ex_a expresion
		| epsilon
	'''

def p_ex_a (p):
	'''
	ex_a : OP_LESS_THAN
		| OP_GREATER_THAN
		| OP_NOT_EQUAL
		| OP_EQUALS
		| OP_GREATER_EQUAL
		| OP_LESS_EQUAL
	'''
	operator_stack.push(operator_dict[p[1]])

def p_quad_helper_cond(p):
	'quad_helper_cond : '
	exp_quad_helper(p, ['<', '>', '!=', '==', '>=', '<='])

def p_exp (p):
	'''
	exp : term quad_helper_sum exp_a
	'''
	print("exp: " + str(p.lexer.lineno))

def p_exp_a (p):
	'''
	exp_a : exp_b exp
		| epsilon
	'''

# Changed position of term 
def p_exp_b (p):
	'''
	exp_b : OP_PLUS
		| OP_MINUS
	'''
	operator_stack.push(operator_dict[p[1]])

def p_quad_helper_sum(p):
	'quad_helper_sum : '
	exp_quad_helper(p, ['+', '-'])

def p_term (p):
	'''
	term : factor quad_helper_mult term_a
	'''
	print("term: " + str(p.lexer.lineno))

def p_term_a (p):
	'''
	term_a : term_b term
		| epsilon
	'''
def p_term_b (p):
	'''
	term_b : OP_TIMES
		| OP_DIVISION
	'''
	operator_stack.push(operator_dict[p[1]])

def p_quad_helper_mult(p):
	'quad_helper_mult : '
	exp_quad_helper(p, ['*', '/'])

def p_factor (p):
	'''
	factor : SEP_LPAR quad_push_lpar condition SEP_RPAR quad_pop_lpar
		| var_cte
	'''
	print("factor: " + str(p.lexer.lineno))

# def p_fact_a(p):
# 	'''
# 	fact_a : exp_b
# 		| epsilon
# 	'''

def p_quad_push_lpar(p):
	'quad_push_lpar : '
	operator_stack.push(special_operator_dict[p[-1]])

def p_quad_pop_lpar(p):
	'quad_pop_lpar : '
	operator_stack.pop()

def p_var_cte(p):
	'''
	var_cte : var_id
		| cnt_prim
	'''

def p_increment (p):
	#exp 			
	'''
	increment : VAR_IDENTIFIER verify_variable double_pushID inc_a inc_var_cte do_sum_rest
	'''

	#push equals
	op = special_operator_dict["="]
	operator_stack.push(op)

	assign_quad_helper()

def p_double_pushID (p):
	'''
	double_pushID : epsilon
	'''

	func = FunctionTable.function_dict[function_stack.peek()]
	type_stack.push(func.vars[p[-2]].type)
	operand_stack.push(func.vars[p[-2]].name)

	func = FunctionTable.function_dict[function_stack.peek()]
	type_stack.push(func.vars[p[-2]].type)
	operand_stack.push(func.vars[p[-2]].name)

def p_do_sum_rest (p):
	'''
	do_sum_rest : epsilon
	'''

	print(p[-2])
	if p[-2] == "+=":
		operator_stack.push(0)
	else:
		operator_stack.push(1)

	exp_quad_helper(p, ['+', '-'])


def p_inc_a (p):
	'''
	inc_a :  OP_PLUS_EQUALS
		| OP_MINUS_EQUALS
	'''

	print(p[1])
	p[0] = p[1]
	

def p_inc_var_cte(p): 
	'''
	inc_var_cte : var_id
		| VAR_INT push_num 
		| exp
	'''
#PROBADO VAR_INT y VAR_IDENTIFIER

def p_if (p):
	'''
	if : IF SEP_LPAR condition SEP_RPAR quad_if_helper do_block if_a if_b end_if_stmt_quad_helper
	'''
def p_if_a (p):
	'''
	if_a : elsif
		| epsilon
	'''
def p_if_b (p):
	'''
	if_b : else
		| epsilon
	'''

def p_quad_if_helper(p):
	'''
	quad_if_helper : epsilon
	'''

	aux = type_stack.pop()
	if aux != 1 :
		Error.not_a_condition(aux, p.lexer.lineno)
	else :
		res = operand_stack.pop()
		operator = special_operator_dict['gotof']

		# Generate Quadruple and push it to the list
		tmp_quad = Quadruple()
		tmp_quad.build(operator, res, None, None)
		Quadruples.push_quad(tmp_quad)

		#Push into jump stack
		Quadruples.push_jump(-1)

		print("PUSH JUMP :")
		Quadruples.print_jump_stack()

def p_elsif (p):
	'''
	elsif : ELSIF end_if_stmt_quad_helper SEP_LPAR condition SEP_RPAR quad_if_helper do_block if_a
	'''

def p_else (p):
	'''
	else : ELSE quad_else_helper do_block
	'''

def p_quad_else_helper(p):
	'''
	quad_else_helper : epsilon
	'''
	operator = special_operator_dict['goto']

	tmp_quad = Quadruple()
	tmp_quad.build(operator, None, None, None)
	Quadruples.push_quad(tmp_quad)

	tmp_false = Quadruples.pop_jump()
	tmp_count = Quadruples.next_free_quad
	tmp_quad = Quadruples.fill_missing_quad(tmp_false, tmp_count)

	Quadruples.push_jump(-1)

def p_end_if_stmt_quad_helper(p):
	'''
	end_if_stmt_quad_helper : epsilon
	'''

	#print("PUSH JUMP BEF POP:")
	Quadruples.print_jump_stack()

	tmp_end = Quadruples.pop_jump()
	#print("POPJUMP")
	print(tmp_end)	
	tmp_count = Quadruples.next_free_quad
	tmp_quad = Quadruples.fill_missing_quad(tmp_end, tmp_count)


def p_condition_block (p):
	'''
	condition_block : SEP_LPAR condition SEP_RPAR do_block
	'''
	print("conditionBlock " + str(p.lexer.lineno))

def p_do_block (p):
	'''
	do_block : DO stmt_loop END
	'''
	print("doBlock " + str(p.lexer.lineno))

# WARNING: Watch out for "figure_creations"
def p_statement (p):
	'''
	statement : assignment 
				| if 
				| cycle 
				| action 
				| camera 
				| function_call 
				| print
				| increment
				| figure_creations 
				| fig_description
				| return
	'''

def p_vars (p):
	'''
	vars : vars_start v_a
	'''

#array
def p_v_a (p):
	'''
	v_a : vars_figs
		| vars_prim
		| vars_arr
	'''

def p_vars_start (p):
	'''
	vars_start : VAR VAR_IDENTIFIER SEP_COLON
	'''
	tmp_var.name = p[2]

def p_vars_figs (p):
	'''
	vars_figs : figure vf_a
	'''
def p_vf_a (p):
	'''
	vf_a : init_fig
		| epsilon
	'''

def p_vars_prim (p):
	'''
	vars_prim : primitive_type var_p_a
	'''
	FunctionTable.add_var_to_func(function_stack.peek(), tmp_var)


def p_var_p_a (p):
	'''
	var_p_a : init_prim
		| epsilon
	'''

def p_init_prim (p):
	'''
	init_prim : push_tmp_var OP_EQUALS push_operator init_a
	'''
	assign_quad_helper()

def p_push_tmp_var(p):
	'push_tmp_var : '
	print_stacks()
	type_stack.push(tmp_var.type)
	operand_stack.push(tmp_var.name)

#array
def p_vars_arr (p):
	'''
	vars_arr : SEP_LBRACKET primitive_type SEP_RBRACKET arr_a
	'''

#array
def p_arr_a (p):
	'''
	arr_a : arr_init_arr
		| init_empty_arr
	'''

#array
#initalization of empty array
def p_init_empty_arr(p):
	'''
	init_empty_arr : 
	'''
	arr_var = Array()
	arr_var.name = tmp_var.name
	arr_var.type = tmp_var.type

	FunctionTable.add_arr_empty_to_func(function_stack.peek(), arr_var)

#array 
#missing array initialization 
def p_arr_init_arr (p):
	'''
	arr_init_arr : SEP_LPAR VAR_INT SEP_RPAR
	'''	
	arr_var = Array()
	arr_var.name = tmp_var.name
	arr_var.type = tmp_var.type
	arr_var.length = p[2]
	FunctionTable.add_arr_complete_to_func(function_stack.peek(), arr_var)


# WARNING: Adds a shift reduce conflict because of function_call
def p_init_a (p):
	'''
	init_a : function_call
		| var_cte
	'''

def p_init_fig (p):
	'''
	init_fig : OP_EQUALS VAR_IDENTIFIER
		| HAS fig_create_block
	'''

def p_fig_create_block (p):
	'''
	fig_create_block : fig_a  END
	'''

def p_fig_a (p):
	'''
	fig_a :  fig_attr fig_b
	'''
def p_fig_b (p):
	'''
	fig_b : SEP_COMMA fig_a
		| epsilon
	'''

def p_fig_attr (p):
	'''
	fig_attr : vector
		| COLOR SEP_COLON VAR_IDENTIFIER
		| SIZE SEP_COLON exp 
	'''

def p_fig_description(p):
	'''
	fig_description : VAR_IDENTIFIER HAS fig_create_block
	'''

def p_vector (p):
	'''
	vector : VAR_VECTORID SEP_COLON SEP_LPAR exp SEP_COMMA exp SEP_RPAR 
	'''

def p_cnt_prim (p):
	'''
	cnt_prim : VAR_INT push_num
		| VAR_DECIMAL push_num
		| VAR_STRING push_string
		| VAR_BOOLEAN push_bool
	'''

def p_return (p):
	'''
	return : RETURN opt_exp
	'''

def p_print (p):
	'''
	print : PRINT push_operator SEP_LPAR print_a SEP_RPAR
	'''
	print("print " + str(p.lexer.lineno))

def p_print_a (p):
	'''
	print_a : exp
		| function_call
	'''
	print_quad_helper()
	
def p_figure_creations (p):
	'''
	figure_creations : VAR VAR_IDENTIFIER SEP_COLON figure HAS fig_create_block
	'''
	pass

def p_var_id(p):
	'var_id : VAR_IDENTIFIER verify_variable push_id'

def p_push_id(p):
	'push_id : '
	var = FunctionTable.get_var_in_scope(function_stack.peek(), p[-2])
	type_stack.push(var.type)
	operand_stack.push(var.name)

def p_push_num(p):
	'push_num : '
	num = eval(p[-1])
	type = 'decimal' if isinstance(num, (float)) else 'int'
	push_const_operand_and_type(num, type)

def p_push_string(p):
	'push_string : '
	push_const_operand_and_type(p[-1], 'string')

def p_push_bool(p):
	'push_bool : '
	push_const_operand_and_type(p[-1], 'boolean')

def p_push_operator(p):
	'push_operator : '
	try:
		op = operator_dict[p[-1]]
	except KeyError:
		op = special_operator_dict[p[-1]]
	operator_stack.push(op)

def p_verify_variable(p):
	'verify_variable : '
	func = function_stack.peek()
	if not FunctionTable.verify_var_in_func(func, p[-1]):
		Error.variable_not_defined(p[-1], p.lexer.lineno)

def p_epsilon(p):
	'epsilon :'
	pass


def p_error(p):
	print "Syntax error at line " + str(p.lexer.lineno) + " Unexpected token  " + str(p.value)
	sys.exit(0)

# MAIN #########################################################################

from virtual_machine import *

parser = yacc.yacc()

if __name__ == '__main__':

	if (len(sys.argv) > 1) : fin = sys.argv[1]
	else : fin = 'input.in'

	f = open(fin, 'r')
	data = f.read()
	# print data
	# print "End of file"
	parser.parse(data, tracking=True)

	print("Successful")

	RUN_AT_LIGHTSPEED()

