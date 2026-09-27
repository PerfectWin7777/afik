fn main() {
    prost_build::compile_protos(&["../ir_spec/widget.proto"], &["../ir_spec"])
        .expect("failed to compile widget.proto");
}
