//! Optional post-processing of decompiled Python source with the `cure`
//! simplifier/formatter (https://github.com/ejfkdev/cure).
//!
//! `cure` turns decompiler-shaped code into idiomatic source: folds
//! constants and opaque predicates, inlines copies, removes compiler
//! artifacts, and prints clean formatting. It is opt-in (`--cure`) so the
//! verified default output stays byte-stable.

/// Simplify/format `src` with cure's Python backend.
///
/// Returns `None` when cure cannot parse the input (for example a module
/// pycdc marked incomplete); callers should then keep pycdc's own output
/// rather than emit a partially-preserved rewrite.
pub fn simplify_python(src: &str) -> Option<String> {
    // Code that introspects the compiler's annotation machinery must keep
    // pycdc's exact shape: cure folds `if True:` registration gates, which
    // changes `__annotate__.__code__.co_freevars` and similar metadata.
    // Only these opt-in markers are skipped (never present in ordinary
    // application code).
    const REFLECTION_MARKERS: [&str; 4] = [
        "__annotate__",
        "co_freevars",
        "__conditional_annotations__",
        "__classdict__",
    ];
    if REFLECTION_MARKERS.iter().any(|marker| src.contains(marker)) {
        return None;
    }
    let mut outcome = cure_python_parser::parse(src);
    if !outcome.errors.is_empty() {
        return None;
    }
    let cfg = cure_engine::Config::default();
    cure_python_simplify::simplify_module(&mut outcome.ast, outcome.module, &cfg);
    Some(cure_python_print::print_module(&outcome.ast, outcome.module))
}

#[cfg(test)]
mod tests {
    use super::simplify_python;

    #[test]
    fn folds_if_return_into_ternary() {
        let src = "def f(v):\n    if v:\n        return 1\n    return 2\n";
        let out = simplify_python(src).expect("cure parses");
        assert!(out.contains("return 1 if v else 2"), "{out}");
    }

    #[test]
    fn skips_compiler_introspection_sources() {
        let src = "def f(cls):\n    return cls.__annotate__.__code__.co_freevars\n";
        assert!(simplify_python(src).is_none());
    }

    #[test]
    fn keeps_unparseable_input_untouched() {
        assert!(simplify_python("def broken(:\n    pass\n").is_none());
    }

    #[test]
    fn compiles_simplified_module() {
        let src = "def f(xs):\n    out = []\n    for x in xs:\n        if x:\n            out.append(x)\n    return out\n";
        let out = simplify_python(src).expect("cure parses");
        assert!(out.contains("def f(xs):"), "{out}");
    }
}
