use super::*;

fn name(value: &str) -> ExprRef {
    Rc::new(Expr::Name(value.into()))
}

fn call(value: &str) -> ExprRef {
    Rc::new(Expr::Call {
        func: name(value), args: Vec::new(), keywords: Vec::new(),
        star_args: None, star_kwargs: None,
    })
}

fn compare(operands: Vec<ExprRef>, ops: Vec<CmpOp>) -> ExprRef {
    Rc::new(Expr::Compare { operands, ops })
}

#[test]
fn extend_accumulated_chain_keeps_all_operands_and_operators() {
    // 0 <= first() <= second(), extended by second() < third() <= 15.
    let zero = Rc::new(Expr::Const(Rc::new(PyObject::Int(0))));
    let limit = Rc::new(Expr::Const(Rc::new(PyObject::Int(15))));
    let first = call("first");
    let second = call("second");
    let third = call("third");
    let left = compare(vec![zero.clone(), first.clone(), second.clone()],
                       vec![CmpOp::LtE, CmpOp::LtE]);
    let right = compare(vec![call("second"), third.clone(), limit.clone()],
                        vec![CmpOp::Lt, CmpOp::LtE]);
    let merged = merge_chain_compare(&left, &right).expect("shared last operand");
    let expected = compare(vec![zero, first, second, third, limit],
                           vec![CmpOp::LtE, CmpOp::LtE, CmpOp::Lt, CmpOp::LtE]);
    assert!(expr_eq(&merged, &expected), "{merged:?}");
}

#[test]
fn matching_an_earlier_operand_does_not_join_unrelated_chains() {
    let left = compare(vec![name("a"), name("b"), name("c")],
                       vec![CmpOp::Lt, CmpOp::LtE]);
    let right = compare(vec![name("b"), name("d")], vec![CmpOp::Lt]);
    assert!(merge_chain_compare(&left, &right).is_none());
}

#[test]
fn retain_every_link_when_repeatedly_extending_a_chain() {
    let mut result = compare(vec![name("a"), name("b")], vec![CmpOp::Lt]);
    let names = ["a", "b", "c", "d", "e", "f"];
    for end in 2..names.len() {
        let right = compare(vec![name(names[end - 1]), name(names[end])],
                            vec![CmpOp::Lt]);
        result = merge_chain_compare(&result, &right).unwrap();
        let expected = compare(names[..=end].iter().map(|n| name(n)).collect(),
                               vec![CmpOp::Lt; end]);
        assert!(expr_eq(&result, &expected));
    }
}

#[test]
fn unchanged_two_operand_chain_and_its_terminal_arm_are_preserved() {
    let left = compare(vec![name("a"), name("b")], vec![CmpOp::Lt]);
    let terminal = merge_chain_compare(&left, &left).unwrap();
    assert!(Rc::ptr_eq(&terminal, &left));
    let right = compare(vec![name("b"), name("c")], vec![CmpOp::LtE]);
    let merged = merge_chain_compare(&left, &right).unwrap();
    let expected = compare(vec![name("a"), name("b"), name("c")],
                           vec![CmpOp::Lt, CmpOp::LtE]);
    assert!(expr_eq(&merged, &expected));
}
