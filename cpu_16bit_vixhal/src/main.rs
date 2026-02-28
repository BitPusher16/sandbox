const NUM_REGISTERS: usize = 8;
const MEMORY_SIZE: usize = 65536;

const FLAG_ZERO: u16 = 1 << 0;
const FLAG_NEGATIVE: u16 = 1 << 1;
const FLAG_OVERFLOW: u16 = 1 << 2;

struct Cpu{
    registers: [u16; NUM_REGISTERS],
    pc: u16,
    sp: u16,
    flags: u16,
    memory: [u8; MEMORY_SIZE],
    halted: bool,
    cycles: u64,
}

#[repr(u8)] // default type for enum discriminant is isize. use attribute to change this.
#[derive(PartialEq, Eq)] // allow comparison.
enum Opcode{
    OP_NOP  = 0x00,  // Do nothing
    OP_LOAD = 0x01,  // Write a number on a sticky note (2-word: next word is the number)
    OP_MOV  = 0x02,  // Copy one sticky note to another
    OP_ADD  = 0x03,  // Add two sticky notes
    OP_SUB  = 0x04,  // Subtract two sticky notes
    OP_AND  = 0x05,  // Bitwise AND
    OP_OR   = 0x06,  // Bitwise OR
    OP_XOR  = 0x07,  // Bitwise XOR
    OP_NOT  = 0x08,  // Bitwise NOT (flip all bits)
    OP_SHL  = 0x09,  // Shift bits left
    OP_SHR  = 0x0A,  // Shift bits right
    OP_CMP  = 0x0B,  // Compare (subtract but only update status board)
    OP_JMP  = 0x0C,  // Jump to task #N
    OP_JZ   = 0x0D,  // Jump IF Zero light is on
    OP_JNZ  = 0x0E,  // Jump IF Zero light is off
    OP_JN   = 0x0F,  // Jump IF Negative light is on
    OP_LDR  = 0x10,  // Load from filing cabinet folder into sticky note
    OP_STR  = 0x11,  // Store sticky note into filing cabinet folder
    OP_PUSH = 0x12,  // Push onto inbox tray
    OP_POP  = 0x13,  // Pop from inbox tray
    OP_CALL = 0x14,  // Bookmark and jump to subroutine (2-word)
    OP_RET  = 0x15,  // Return from subroutine (pop bookmark)
    OP_HALT = 0x16,  // Go home (stop CPU)
}

fn DECODE_OPCODE(instr: u16) -> u16 { (instr >> 11) & 0x1F }
fn DECODE_DST   (instr: u16) -> u16 { (instr >>  8) & 0x07 }
fn DECODE_SRC   (instr: u16) -> u16 { (instr >>  5) & 0x07 }
fn DECODE_IMM5  (instr: u16) -> u16 { instr & 0x01F }
fn DECODE_ADDR  (instr: u16) -> u16 { instr & 0x7FF }

fn ENCODE_REG   (op: Opcode, dst: u8, src: u8, imm5: u8) -> u16 {
    ((op as u16 & 0x1F) << 11) | ((dst as u16 & 0x7) << 8) | ((src as u16 & 0x7) << 5) | (imm5 as u16 & 0x1F)
}

fn ENCODE_JMP   (op: Opcode, address: u16) -> u16 {
    ((op as u16) << 11) | (address & 0x7FF)
}

fn mem_read16(cpu: & Cpu, address: u16) -> u16{
    let low: u16 = cpu.memory[address as usize] as u16;
    let high: u16 = cpu.memory[address as usize + 1] as u16;
    (high << 8) | low
}

fn mem_write16(cpu: &mut Cpu, address: u16, value: u16){
    cpu.memory[address as usize] = (value & 0xFF) as u8;
    cpu.memory[address as usize + 1] = ((value >> 8) & 0xFF) as u8;
}

fn update_flags(cpu: &mut Cpu, result: u16, a: u16, b: u16, op: Opcode){
    cpu.flags = 0;

    if(result == 0){ cpu.flags |= FLAG_ZERO; }
    if(result & 0x8000 > 0){ cpu.flags |= FLAG_NEGATIVE; }

    if(op == Opcode::OP_ADD){
        if((a ^ result) & (b ^ result) & 0x8000 > 0){ cpu.flags |= FLAG_OVERFLOW; }
    }
    else if(op == Opcode::OP_SUB || op == Opcode::OP_CMP){
        if((a ^ b) & (a ^ result) & 0x8000 > 0){ cpu.flags |= FLAG_OVERFLOW; }
    }
}

fn alu_execute(cpu: &mut Cpu, op: Opcode, a: u16, b: u16) -> u16{
    let mut result: u16 = 0;
    match (op) {
        Opcode::OP_ADD => {result = a + b;},
        Opcode::OP_SUB => {result = a - b;},
        Opcode::OP_CMP => {result = a - b;},
        Opcode::OP_AND => {result = a & b;},
        Opcode::OP_OR  => {result = a | b;},
        Opcode::OP_XOR => {result = a ^ b;},
        Opcode::OP_NOT => {result = !a;},
        Opcode::OP_SHL => {result = a << (b & 0xF);},
        Opcode::OP_SHR => {result = a >> (b & 0xF);},
        _ => {}
    }
    update_flags(cpu, result, a, b, op);
    result
}


fn main() {
    println!("Hello, world!");
}




















