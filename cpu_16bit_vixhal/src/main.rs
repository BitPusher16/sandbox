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
    //memory: Memory,
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

fn u16_to_opcode(u: u16) -> Opcode{
    match u{
        0x00 =>  Opcode::OP_NOP ,
        0x01 =>  Opcode::OP_LOAD,
        0x02 =>  Opcode::OP_MOV ,
        0x03 =>  Opcode::OP_ADD ,
        0x04 =>  Opcode::OP_SUB ,
        0x05 =>  Opcode::OP_AND ,
        0x06 =>  Opcode::OP_OR  ,
        0x07 =>  Opcode::OP_XOR ,
        0x08 =>  Opcode::OP_NOT ,
        0x09 =>  Opcode::OP_SHL ,
        0x0A =>  Opcode::OP_SHR ,
        0x0B =>  Opcode::OP_CMP ,
        0x0C =>  Opcode::OP_JMP ,
        0x0D =>  Opcode::OP_JZ  ,
        0x0E =>  Opcode::OP_JNZ ,
        0x0F =>  Opcode::OP_JN  ,
        0x10 =>  Opcode::OP_LDR ,
        0x11 =>  Opcode::OP_STR ,
        0x12 =>  Opcode::OP_PUSH,
        0x13 =>  Opcode::OP_POP ,
        0x14 =>  Opcode::OP_CALL,
        0x15 =>  Opcode::OP_RET ,
        0x16 =>  Opcode::OP_HALT,
        _    =>  Opcode::OP_HALT
    }
}

fn DECODE_OPCODE(instr: u16) -> u16 { (instr >> 11) & 0x1F }
fn DECODE_DST   (instr: u16) -> u16 { (instr >>  8) & 0x07 }
fn DECODE_SRC   (instr: u16) -> u16 { (instr >>  5) & 0x07 }
fn DECODE_IMM5  (instr: u16) -> u16 { instr & 0x01F }
fn DECODE_ADDR  (instr: u16) -> u16 { instr & 0x7FF }

fn ENCODE_REG   (op: Opcode, dst: u16, src: u16, imm5: u16) -> u16 {
    ((op as u16 & 0x1F) << 11) | ((dst as u16 & 0x7) << 8) | ((src as u16 & 0x7) << 5) | (imm5 as u16 & 0x1F)
}

fn ENCODE_JMP   (op: Opcode, address: u16) -> u16 {
    ((op as u16) << 11) | (address & 0x7FF)
}

fn mem_read16(cpu: & Cpu, address: u16) -> u16{
    let low: u16 = cpu.memory[address as usize] as u16;
    let high: u16 = cpu.memory[(address + 1) as usize] as u16;
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

fn cpu_step(cpu: &mut Cpu){
    if(cpu.halted){return;}

    let instruction: u16 = mem_read16(cpu, cpu.pc);
    let opcode: Opcode = u16_to_opcode(DECODE_OPCODE(instruction));
    let dst = DECODE_DST(instruction);
    let src = DECODE_SRC(instruction);
    let imm5 = DECODE_IMM5(instruction);
    let addr = DECODE_ADDR(instruction);

    cpu.pc += 2;

    match(opcode){
        Opcode::OP_NOP => {},
        Opcode::OP_LOAD => {
            cpu.registers[dst as usize] = mem_read16(cpu, cpu.pc);
            cpu.pc += 2;
        },
        Opcode::OP_MOV => {
            cpu.registers[dst as usize] = cpu.registers[src as usize];
        },
        Opcode::OP_ADD => {
            cpu.registers[dst as usize] = alu_execute(
                cpu, Opcode::OP_ADD, cpu.registers[dst as usize], cpu.registers[src as usize]);
        },
        Opcode::OP_SUB => {
            cpu.registers[dst as usize] = alu_execute(
                cpu, Opcode::OP_SUB, cpu.registers[dst as usize], cpu.registers[src as usize]);
        },
        Opcode::OP_AND => {
            cpu.registers[dst as usize] = alu_execute(
                cpu, Opcode::OP_AND, cpu.registers[dst as usize], cpu.registers[src as usize]);
        },
        Opcode::OP_OR => {
            cpu.registers[dst as usize] = alu_execute(
                cpu, Opcode::OP_OR, cpu.registers[dst as usize], cpu.registers[src as usize]);
        },
        Opcode::OP_XOR => {
            cpu.registers[dst as usize] = alu_execute(
                cpu, Opcode::OP_XOR, cpu.registers[dst as usize], cpu.registers[src as usize]);
        },
        Opcode::OP_NOT => {
            cpu.registers[dst as usize] = alu_execute(
                cpu, Opcode::OP_NOT, cpu.registers[dst as usize], 0);
        },
        Opcode::OP_SHL => {
            cpu.registers[dst as usize] = alu_execute(
                cpu, Opcode::OP_SHL, cpu.registers[dst as usize], imm5);
        },
        Opcode::OP_SHR => {
            cpu.registers[dst as usize] = alu_execute(
                cpu, Opcode::OP_SHR, cpu.registers[dst as usize], imm5);
        },
        Opcode::OP_CMP => {
            cpu.registers[dst as usize] = alu_execute(
                cpu, Opcode::OP_CMP, cpu.registers[dst as usize], cpu.registers[src as usize]);
        },
        Opcode::OP_JMP => {
            cpu.pc = addr;
        },
        Opcode::OP_JZ => {
            if(cpu.flags & FLAG_ZERO > 0){ cpu.pc = addr;}
        },
        Opcode::OP_JNZ => {
            if(!(cpu.flags & FLAG_ZERO > 0)){ cpu.pc = addr;}
        },
        Opcode::OP_JN => {
            if(cpu.flags & FLAG_NEGATIVE > 0){ cpu.pc = addr;}
        },
        Opcode::OP_LDR => {
            cpu.registers[dst as usize] = mem_read16(cpu, cpu.registers[src as usize]);
        },
        Opcode::OP_STR => {
            mem_write16(cpu, cpu.registers[dst as usize], cpu.registers[src as usize]);
        },
        Opcode::OP_PUSH => {
            cpu.sp -= 2;
            mem_write16(cpu, cpu.sp, cpu.registers[dst as usize]);
        },
        Opcode::OP_POP => {
            cpu.registers[dst as usize] = mem_read16(cpu, cpu.sp);
            cpu.sp += 2;
        },
        Opcode::OP_CALL => {
            let target: u16 = mem_read16(cpu, cpu.pc);
            cpu.pc += 2;
            cpu.sp -= 2;
            mem_write16(cpu, cpu.sp, cpu.pc);
            cpu.pc = target;
        },
        Opcode::OP_RET => {
            cpu.pc = mem_read16(cpu, cpu.sp);
            cpu.sp += 2;
        },
        Opcode::OP_HALT => {
            cpu.halted = true;
        },
    }
    cpu.cycles += 1;
}

fn cpu_run(cpu: &mut Cpu){
    while(!cpu.halted){
        cpu_step(cpu);
    }
}

//#[derive(Debug, Clone)]
pub struct Label {
    pub name: String,
    pub address: u16,
}

fn parse_register(s: &str) -> u16 {
    let s = s.trim_start_matches([' ', '\t']);
    let s = s.splitn(2, ',').next().unwrap_or("").trim_end();
    let s = &s[..s.len().min(15)];
    let bytes = s.as_bytes();
    if bytes.len() == 2
        && (bytes[0] == b'R' || bytes[0] == b'r')
        && bytes[1].is_ascii_digit()
        && (bytes[1] - b'0') <= 7
    {
        (bytes[1] - b'0') as u16
    } else {
        65535
    }
}

fn parse_immediate(s: &str) -> u16 {
    let s = s.trim_start_matches([' ', '\t']);
    s.parse::<u16>().unwrap_or(0)
}

fn assemble(source: &str, max_words: usize) -> Vec<u16> {
    let mut labels: Vec<Label> = Vec::new();
    let mut output: Vec<u16> = Vec::new();

    // PASS 1: record label positions
    let mut addr: u16 = 0;
    for line in source.lines() {
        let t = line.trim_start_matches([' ', '\t']);
        if t.is_empty() || t.starts_with(';') {
            continue;
        }
        if let Some(colon_pos) = t.find(':') {
            if colon_pos + 1 == t.len() {
                labels.push(Label {
                    name: t[..colon_pos].to_string(),
                    address: addr,
                });
                continue;
            }
        }
        let mn = t.split_whitespace().next().unwrap_or("").to_uppercase();
        if mn == "LOAD" || mn == "CALL" {
            addr += 4;
        } else {
            addr += 2;
        }
    }

    // PASS 2: emit instructions
    for line in source.lines() {
        if output.len() >= max_words {
            break;
        }
        let t = line.trim_start_matches([' ', '\t']);
        if t.is_empty() || t.starts_with(';') || t.contains(':') {
            continue;
        }

        // Parse mnemonic and up to two args
        let mut parts = t.splitn(2, char::is_whitespace);
        let mn = parts.next().unwrap_or("").to_uppercase();
        let rest = parts.next().unwrap_or("").trim();
        let (a1, a2) = if let Some(comma) = rest.find(',') {
            (rest[..comma].trim(), rest[comma + 1..].trim())
        } else {
            (rest, "")
        };

        let resolve_label = |name: &str| -> u16 {
            labels
                .iter()
                .find(|l| l.name == name)
                .map(|l| l.address)
                .unwrap_or_else(|| name.parse::<u16>().unwrap_or(0))
        };

        match mn.as_str() {
            "NOP"  => output.push(ENCODE_REG(Opcode::OP_NOP,  0, 0, 0)),
            "HALT" => output.push(ENCODE_REG(Opcode::OP_HALT, 0, 0, 0)),
            "RET"  => output.push(ENCODE_REG(Opcode::OP_RET,  0, 0, 0)),
            "LOAD" => {
                output.push(ENCODE_REG(Opcode::OP_LOAD, parse_register(a1), 0, 0));
                output.push(parse_immediate(a2) as u16);
            }
            "MOV"  => output.push(ENCODE_REG(Opcode::OP_MOV,  parse_register(a1), parse_register(a2), 0)),
            "ADD"  => output.push(ENCODE_REG(Opcode::OP_ADD,  parse_register(a1), parse_register(a2), 0)),
            "SUB"  => output.push(ENCODE_REG(Opcode::OP_SUB,  parse_register(a1), parse_register(a2), 0)),
            "AND"  => output.push(ENCODE_REG(Opcode::OP_AND,  parse_register(a1), parse_register(a2), 0)),
            "OR"   => output.push(ENCODE_REG(Opcode::OP_OR,   parse_register(a1), parse_register(a2), 0)),
            "XOR"  => output.push(ENCODE_REG(Opcode::OP_XOR,  parse_register(a1), parse_register(a2), 0)),
            "NOT"  => output.push(ENCODE_REG(Opcode::OP_NOT,  parse_register(a1), 0, 0)),
            "SHL"  => output.push(ENCODE_REG(Opcode::OP_SHL,  parse_register(a1), 0, parse_immediate(a2))),
            "SHR"  => output.push(ENCODE_REG(Opcode::OP_SHR,  parse_register(a1), 0, parse_immediate(a2))),
            "CMP"  => output.push(ENCODE_REG(Opcode::OP_CMP,  parse_register(a1), parse_register(a2), 0)),
            "LDR"  => output.push(ENCODE_REG(Opcode::OP_LDR,  parse_register(a1), parse_register(a2), 0)),
            "STR"  => output.push(ENCODE_REG(Opcode::OP_STR,  parse_register(a1), parse_register(a2), 0)),
            "PUSH" => output.push(ENCODE_REG(Opcode::OP_PUSH, parse_register(a1), 0, 0)),
            "POP"  => output.push(ENCODE_REG(Opcode::OP_POP,  parse_register(a1), 0, 0)),
            "JMP" | "JZ" | "JNZ" | "JN" => {
                let jop = match mn.as_str() {
                    "JMP" => Opcode::OP_JMP,
                    "JZ"  => Opcode::OP_JZ,
                    "JNZ" => Opcode::OP_JNZ,
                    _     => Opcode::OP_JN,
                };
                let target = resolve_label(a1);
                output.push(ENCODE_JMP(jop, target));
            }
            "CALL" => {
                let target = resolve_label(a1);
                output.push(ENCODE_REG(Opcode::OP_CALL, 0, 0, 0));
                output.push(target);
            }
            other => eprintln!("Secretary can't understand: {}", other),
        }
    }

    output
}

fn load_program(cpu: &mut Cpu, words: Vec<u16>){
    for (idx, word_addr) in words.iter().enumerate(){
        mem_write16(cpu, (idx*2) as u16, *word_addr);
    }

    // alternatively:
    //for (idx, &word) in words.iter().enumerate(){
    //    mem_write16(cpu, (idx*2) as u16, word);
    //}
}

fn cpu_dump(cpu: & Cpu) {
    println!("\n=== DESK STATUS ===");
    for (i, &reg) in cpu.registers.iter().enumerate() {
        println!("  Sticky note R{} = {} (0x{:04X})", i, reg, reg);
    }
    println!("  Checklist position: 0x{:04X}", cpu.pc);
    println!("  Inbox tray position: 0x{:04X}", cpu.sp);
    println!("  Status board: [{}{}{}]",
        if cpu.flags & FLAG_OVERFLOW != 0 { 'O' } else { '-' },
        if cpu.flags & FLAG_NEGATIVE != 0 { 'N' } else { '-' },
        if cpu.flags & FLAG_ZERO     != 0 { 'Z' } else { '-' },
    );
    println!("  Tasks completed: {}", cpu.cycles);
}


fn main() {
    println!("=== 16-BIT CPU EMULATOR ===");
    println!("=== The Office Worker Simulation ===\n");

    let mut cpu = Cpu{
        registers: [0;NUM_REGISTERS],
        pc: 0,
        sp: 0xFFFF,
        flags: 0,
        memory:[0;MEMORY_SIZE],
        halted: false,
        cycles: 0
    };

    let program = "\
        ; Sum of 1 to 100: answer ends up on sticky note R0\n\
        ; Demonstrates: full LOAD, memory access, stack operations\n\
        LOAD R0, 0\n\
        LOAD R1, 100\n\
        LOAD R2, 1\n\
        LOAD R3, 0\n\
        LOAD R4, 1000\n\
        loop:\n\
        ADD R0, R1\n\
        SUB R1, R2\n\
        CMP R1, R3\n\
        JNZ loop\n\
        STR R4, R0\n\
        PUSH R0\n\
        LOAD R0, 0\n\
        POP R0\n\
        LDR R5, R4\n\
        HALT\n\
    ";

    let program3 = "\
        LOAD R0, 0\n\
        LOAD R1, 100\n\
        LOAD R2, 1\n\
        LOAD R3, 0\n\
        LOAD R4, 1000\n\
        HALT\n\
    ";

    println!("=== Program: ===");
    print!("{}\n", program);

    //let mut machine_code: Vec<u16> = Vec::new();
    let machine_code = assemble(program, 512);

    println!("=== Task forms (machine code): ===");
    for (i, &word) in machine_code.iter().enumerate() {
        println!("Word [{:02}] @ 0x{:04X}: 0x{:04X}", i, i * 2, word);
    }
    println!("");

    load_program(&mut cpu, machine_code);
    println!("=== Worker starts... ===");
    cpu_run(&mut cpu);
    cpu_dump(&mut cpu);
    println!("");

    println!("=== VERIFICATION ===");
    println!("R0 (register) = {} {}", cpu.registers[0], cpu.registers[0] == 5050);
    println!("R4 (register) = {} {}", cpu.registers[4], cpu.registers[4] == 1000);
    println!("R5 (register) = {} {}", cpu.registers[5], cpu.registers[5] == 5050);
    let mem_result = mem_read16(&cpu, 1000);
    println!("Memory[1000]  = {} {}", mem_result, mem_result == 5050);

}


















