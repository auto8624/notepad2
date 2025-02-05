#include "EditLexer.h"
#include "EditStyleX.h"

static KEYWORDLIST Keywords_LLVM = {{
//++Autogenerated -- start of section automatically generated
"alias appending asm attributes available_externally comdat common constant datalayout declare define distinct "
"extern_weak external false gc global ifunc internal linkonce linkonce_odr module none null "
"partition poison prefix private section source_filename target triple true undef uselistorder uselistorder_bb "
"weak weak_odr "

, // 1 type
"bfloat double float fp128 half i1 i128 i16 i32 i64 i8 label metadata opaque ppc_fp128 ptr token type void vscale "
"x86_fp80 x86_mmx "

, // 2 attribute
"acq_rel acquire addrspace( afn "
"align align( alignstack alignstack( allocalign allockind( allocptr allocsize( alwaysinline any anyregcc arcp argmemonly "
"atomic "
"blockaddress( builtin byval byval( ccc cfguard_checkcc cold coldcc contract convergent cxx_fast_tlscc "
"default denormal-fp-math denormal-fp-math-f32 dereferenceable( dereferenceable_or_null( "
"disable_sanitizer_instrumentation dllexport dllimport dontcall-error dontcall-warn "
"dso_local dso_local_equivalent dso_preemptable "
"exact exactmatch fast fastcc fn_ret_thunk_extern frame-pointer hidden hot "
"immarg inaccessiblemem_or_argmemonly inaccessiblememonly inalloca inbounds indirect-tls-seg-refs initialexec inlinehint "
"inrange inreg inteldialect "
"jumptable largest local_unnamed_addr localdynamic localexec min-legal-vector-width minsize monotonic mustprogress "
"naked nest ninf nnan no-inline-line-tables no-jump-tables no-stack-arg-probe "
"no_cfi no_sanitize_address no_sanitize_hwaddress noalias nobuiltin nocapture nocf_check noduplicate noduplicates nofree "
"noimplicitfloat noinline nomerge nonlazybind nonnull norecurse noredzone noreturn "
"nosanitize_bounds nosanitize_coverage nosync noundef nounwind nsw nsz null_pointer_is_valid nuw "
"optforfuzzing optnone optsize "
"patchable-function personality preallocated( preserve_allcc preserve_mostcc probe-stack prologue protected "
"readnone readonly reassoc release returned returns_twice "
"safestack samesize "
"sanitize_address sanitize_address_dyninit sanitize_hwaddress sanitize_memory sanitize_memtag sanitize_thread seq_cst "
"shadowcallstack sideeffect signext speculatable speculative_load_hardening sret ssp sspreq sspstrong "
"stack-probe-size strictfp swiftasync swiftcc swifterror swiftself swifttailcc syncscope( "
"tailcc thread_local( thunk unnamed_addr unordered uwtable vector-function-abi-variant volatile vscale_range( "
"warn-stack-size webkit_jscc willreturn writeonly zeroext zeroinitializer "

, // 3 instruction
"add addrspacecast alloca and ashr atomicrmw bitcast br "
"call callbr caller catch catchpad catchret catchswitch cleanup cleanuppad cleanupret cmpxchg "
"eq extractelement extractvalue "
"fadd fcmp fdiv fence filter fmax fmin fmul fneg fpext fptosi fptoui fptrunc freeze frem from fsub getelementptr "
"icmp indirectbr insertelement insertvalue inttoptr invoke landingpad load lshr max min mul musttail nand ne notail "
"oeq oge ogt ole olt one or ord phi ptrtoint resume ret "
"sdiv select sext sge sgt shl shufflevector sitofp sle slt srem store sub switch tail to trunc "
"udiv ueq uge ugt uitofp ule ult umax umin une uno unreachable unwind urem va_arg within xchg xor zext "

, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
//--Autogenerated -- end of section automatically generated
}};

static EDITSTYLE Styles_LLVM[] = {
	EDITSTYLE_DEFAULT,
	{ SCE_LLVM_WORD, NP2StyleX_Keyword, L"fore:#0000FF" },
	{ SCE_LLVM_WORD2, NP2StyleX_TypeKeyword, L"fore:#0000FF" },
	{ SCE_LLVM_INTRINSIC, NP2StyleX_Intrinsic, L"bold; fore:#A46000" },
	{ SCE_LLVM_INSTRUCTION, NP2StyleX_Instruction, L"fore:#0080FF" },
	{ MULTI_STYLE(SCE_LLVM_ATTRIBUTE, SCE_LLVM_ATTRIBUTE_GROUP, 0, 0), NP2StyleX_Attribute, L"fore:#FF8000" },
	{ MULTI_STYLE(SCE_LLVM_METADATA, SCE_LLVM_META_STRING, 0, 0), NP2StyleX_Metadata, L"fore:#FF8000" },
	{ SCE_LLVM_COMDAT, NP2StyleX_COMDAT, L"fore:#BB60D5" },
	{ MULTI_STYLE(SCE_LLVM_GLOBAL_VARIABLE, SCE_LLVM_QUOTED_GLOBAL_VARIABLE, 0, 0), NP2StyleX_GlobalVariable, L"fore:#7C5AF3" },
	{ MULTI_STYLE(SCE_LLVM_VARIABLE, SCE_LLVM_QUOTED_VARIABLE, 0, 0), NP2StyleX_Variable, L"fore:#808000" },
	{ SCE_LLVM_FUNCTION, NP2StyleX_Function, L"fore:#A46000" },
	{ SCE_LLVM_TYPE, NP2StyleX_Type, L"bold; fore:#007F7F" },
	{ SCE_LLVM_COMMENTLINE, NP2StyleX_Comment, L"fore:#608060" },
	{ SCE_LLVM_STRING, NP2StyleX_String, L"fore:#008000" },
	{ SCE_LLVM_ESCAPECHAR, NP2StyleX_EscapeSequence, L"fore:#0080C0" },
	{ SCE_LLVM_LABEL, NP2StyleX_Label, L"back:#FFC040" },
	{ SCE_LLVM_NUMBER, NP2StyleX_Number, L"fore:#FF0000" },
	{ SCE_LLVM_OPERATOR, NP2StyleX_Operator, L"fore:#B000B0" },
};

EDITLEXER lexLLVM = {
	SCLEX_LLVM, NP2LEX_LLVM,
//Settings++Autogenerated -- start of section automatically generated
	{
		LexerAttr_NoBlockComment,
		TAB_WIDTH_4, INDENT_WIDTH_4,
		(1 << 0) | (1 << 1), // level1, level2
		0,
		'\\', SCE_LLVM_ESCAPECHAR, 0,
		0,
		0, 0,
		SCE_LLVM_OPERATOR, 0
		, KeywordAttr32(0, KeywordAttr_PreSorted) // keywords
		| KeywordAttr32(1, KeywordAttr_PreSorted) // type
		| KeywordAttr32(2, KeywordAttr_PreSorted) // attribute
		| KeywordAttr32(3, KeywordAttr_PreSorted) // instruction
	},
//Settings--Autogenerated -- end of section automatically generated
	EDITLEXER_HOLE(L"LLVM IR", Styles_LLVM),
	L"ll",
	&Keywords_LLVM,
	Styles_LLVM
};
