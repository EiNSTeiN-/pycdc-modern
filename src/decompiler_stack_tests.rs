use super::*;
use crate::pyc::PycModule;

fn context(code: &CodeObject, version: PythonVersion, instrs: Vec<Instruction>) -> Ctx<'_> {
    Ctx {
        code,
        table: table_for(version).unwrap(),
        version,
        instrs,
        idx_of: Default::default(),
        targets: Default::default(),
        stack: Vec::new(),
        blocks: vec![Block::new(BlockType::Main, 0, usize::MAX)],
        clean: true,
        unpack_frames: Vec::new(),
        comp_target_store: false,
        await_mode: false,
        pending_async_with_ctx: None,
        skip_end_send: false,
        with_exit_await_drop: false,
        with_handler_starts: std::collections::HashSet::new(),
        async_for_guard: None,
        legacy_nest: Vec::new(),
        legacy_nest_depth: 0,
        py26_temps: HashMap::new(),
        completed_comp_regions: Vec::new(),
        last_py26_temp: None,
        as_cleanup_wrappers: Vec::new(),
        used_exc_info: false,
        region_collect_only: false,
        skipped_chain_landing: None,
        pending_gen_code: None,
        recent_code_const: None,
        pending_match_class: None,
        last_kw_names: Vec::new(),
        globals: Vec::new(),
        nonlocals: Vec::new(),
        exc_entries: Vec::new(),
        raw_exc_entries: Vec::new(),
        try_ctxs: HashMap::new(),
        handler_zone: None,
        chain_heads: Default::default(),
        with_regions: Default::default(),
        with_region_handlers: Default::default(),
        active_try: None,
        active_try_stack: Vec::new(),
        last_try_body_end: None,
        pending_try_tail: None,
        pending_post_chain_stmt: None,
        tail_pair_at: None,
        pending_try_ctx: None,
        emitting_try: std::collections::HashSet::new(),
        fin_copy_guard: None,
        pending_nested_finally: None,
        nested_inner_handlers: Vec::new(),
        legacy_try: None,
        legacy_handler: None,
        legacy_handler_end: None,
        legacy_handler_name_store: false,
        legacy_handler_cleanup: false,
        fused_guard_pad_at: std::collections::HashSet::new(),
        swallowed_cleanup_del: None,
        in_handler_prelude: false,
        pending_then: Vec::new(),
        pending_handlers: Vec::new(),
        pending_try_body: Vec::new(),
        pending_orelse_mark: None,
        return_offsets: std::collections::HashSet::new(),
        legacy_body_redirect: None,
        pending_loop_close_at_chain: None,
        chain_absorb_body: None,
        sunk_return_fold_at: None,
        sunk_loop_return_lift: false,
        sunk_pair_drop: None,
        sunk_while_lift: None,
        nested_tail_defer: false,
        pending_try_handlers: Vec::new(),
        pending_loop: Vec::new(),
        pending_with: Vec::new(),
        pending_try_orelse: Vec::new(),
        with_exits: 0,
        pending_print: Vec::new(),
        pending_print_dest: None,
        unpack_targets: FrameTargets(Vec::new()),
        unpack_target_lines: Vec::new(),
        pending_unpack_wrap: Vec::new(),
        awaiting_for_target: false,
        pending_if_stmts: Vec::new(),
        cur_offset: 0,
        cur_next: 0,
        prev_op: None,
        prev_op_at_exec: None,
        skip_until: None,
        import_star_pop_pending: false,
        cond_jump_redirect: std::collections::HashMap::new(),
        dup_copy_redirect: HashMap::new(),
        dup_copy_skip: Vec::new(),
        broken_loop_top: None,
        py2_else_pop_at: None,
        pending_star_kw_call: false,
        threaded_break_at: HashSet::new(),
        closed_loop_tops: Vec::new(),
        while_true_loops: Vec::new(),
        or_rot_revals: Vec::new(),
        bare_try_parse: false,
        handler_sunk_tail: Vec::new(),
        dup_tail_ternary_skip: None,
        pending_as_cleanup: None,
        star_tail: Vec::new(),
        star_tail_end: None,
        region_result_expr: None,
        held_cleanup_store: None,
        class_scope: Vec::new(),
        inline_comp: None,
        inline_comp_stack: Vec::new(),
        pending_restore_vars: Vec::new(),
        comp_restore_vars: Vec::new(),
        cur_line: None,
        pending_stores: Vec::new(),
        last_store_line: None,
        group_start: 0,
        last_flush_offset: 0,
        flushing: false,
        pending_aug: None,
        pending_decorators: Vec::new(),
        pending_class_decorators: Vec::new(),
        pending_py2_class: None,
        import_names: Vec::new(),
        dotted_as_just_emitted: false,
        import_module: None,
    }
}

fn instruction(op: Op, arg: u32) -> Instruction {
    Instruction {
        offset: 0, start: 0, size: 2, opcode: 0, op, arg,
        has_arg: true, target: None, is_backward: false, line: None,
    }
}

fn fixture() -> PycModule {
    PycModule::from_bytes(include_bytes!("../tests/pyc/comprehensions.3.11.pyc")).unwrap()
}

#[test]
fn copy_keeps_one_evaluation_and_swap_reorders_without_losing_operands() {
    let module = fixture();
    // The intermediate stack in `lower <= read() <= upper` is reordered
    // and copied so the middle expression is evaluated exactly once.
    let lower = Rc::new(Expr::Name("lower".into()));
    let middle = Rc::new(Expr::Call {
        func: Rc::new(Expr::Name("read".into())), args: Vec::new(),
        keywords: Vec::new(), star_args: None, star_kwargs: None,
    });
    for minor in 11..=14 {
        let version = PythonVersion { minor, ..module.version() };
        let ctx = context(&module.code, version,
            vec![instruction(Op::SWAP, 2), instruction(Op::COPY, 2)]);
        let result = ctx.sim_stack_region(0, 2, vec![lower.clone(), middle.clone()])
            .expect("COPY and SWAP are available from Python 3.11");
        assert_eq!(result.len(), 3);
        assert!(Rc::ptr_eq(&result[0], &middle));
        assert!(Rc::ptr_eq(&result[1], &lower));
        assert!(Rc::ptr_eq(&result[2], &middle));
    }
}

#[test]
fn copy_and_swap_respect_deeper_stack_entries_and_region_boundaries() {
    let module = fixture();
    let values: Vec<_> = ["callee", "argument", "value"].iter()
        .map(|name| Rc::new(Expr::Name((*name).into()))).collect();
    let ctx = context(&module.code, module.version(), vec![
        instruction(Op::SWAP, 3), instruction(Op::COPY, 3),
        instruction(Op::STORE_FAST, 0),
    ]);
    let result = ctx.sim_stack_region(0, 2, values.clone()).unwrap();
    assert_eq!(result.len(), 4);
    for (index, source) in [2, 1, 0, 2].iter().enumerate() {
        assert!(Rc::ptr_eq(&result[index], &values[*source]));
    }
    // Simulation must still reject a region that includes a statement.
    assert!(ctx.sim_stack_region(0, 3, values).is_none());
}

#[test]
fn copy_and_swap_reject_zero_depth_and_stack_underflow() {
    let module = fixture();
    for op in [Op::COPY, Op::SWAP] {
        for (depth, length) in [(0, 0), (0, 1), (1, 0), (2, 1), (u32::MAX, 1)] {
            let ctx = context(&module.code, module.version(), vec![instruction(op, depth)]);
            let values = vec![Rc::new(Expr::Name("value".into())); length];
            assert!(ctx.sim_stack_region(0, 1, values).is_none(), "{op:?} {depth}");
        }
    }
}

#[test]
fn top_copy_and_identity_swap_are_valid() {
    let module = fixture();
    let value = Rc::new(Expr::Name("value".into()));
    let ctx = context(&module.code, module.version(),
        vec![instruction(Op::COPY, 1), instruction(Op::SWAP, 1)]);
    let result = ctx.sim_stack_region(0, 2, vec![value.clone()]).unwrap();
    assert_eq!(result.len(), 2);
    assert!(result.iter().all(|entry| Rc::ptr_eq(entry, &value)));
}
