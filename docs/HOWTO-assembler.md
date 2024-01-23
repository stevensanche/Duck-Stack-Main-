# Assembler Phase 1 

Very few people can write machine code directly, and 
fewer still would choose to.  When it is necessary to write
code for a particular machine instruction-by-instruction, 
we write it in assembly language, a textual notation in 
which we can write mnemonic abbreviations like ADD instead 
of calculating the numeric value of an instruction. 

As long as we're writing in a more readable notation and letting 
the computer translate it to machine code, we might as well let it 
take care of some other details: 

* Instead of writing referring to an address as a number, 
we would like to label some lines in the code and refer 
to the labels.  

* Instead of writing a jump with notation like "ADD r15,r0,r15[3]", 
we would like to create a pseudo-instruction code like JUMP to 
make the code clearer.  Putting this together with the prior step, 
instead of writing

    ```
         ADD    r1,r1,0[2]      # Count up r1 by 2
         STORE  r1,r0,r0[511]    # ... printing each value    
         SUB    r0,r1,r0[10]     # ... r1 > 10 ? 
         ADD/P  r15,0,r15[-3]    # repeat until r1 > 10
   ```
   
   we should be able to write the same instructions as 
   
   ```
   again: ADD    r1,r1,0[2]      # Count up r1 by 2
          STORE  r1,r0,r0[511]    # ... printing each value    
          SUB    r0,r1,r0[10]     # ... r1 > 10 ? 
          JUMP/P again            # repeat until r1 > 10
  ```
  
   The JUMP instruction should be automatically translated 
   into the corresponding ADD instruction, with the address 
   *again* translated into the relative address (that is, 
   change in program counter) -3.  

    We should be able to similarly
    use symbolic labels for data locations and in LOAD and STORE
    operations. Instead of 

    ```
        LOAD  r1,r0,r15[3]   # x is 3 locations ahead
        STORE r1,r0,r0[511]  # Print it
        HALT r0,r0,r0
    x:  DATA  42
    ```

    I'd like to write 
    
    ```
        LOAD  r1,x
        STORE r1,r0,r0[511]  # Print it
        HALT r0,r0,r0
    x:  DATA  42
    ```
    
# Assembler Phase II

I have provided `assembler_phase2.py`, which takes the 
*fully resolved* assembly code and produces object code.  By *fully
resolved* I mean that it does not contain the short-cuts described 
above.  There are no pseudo-instructions like JUMP, and all the 
addresses are provided in numeric form.  

Assembler Phase II serves two purposes.  First, if we can translate 
the pseudo-instruction codes into real Duck Machine instruction codes, 
and replace labels with the addresses they represent, then Assembler Phase II 
will take care of the rest of the translation of assembly code to 
machine code.  

In addition, Assembler Phase II serves as a useful 
model for Assembler Phase I, and has a good deal of code that we can 
copy with or without modifications.  

## The Promise and Peril of Cut-and-Paste Programming

Programmers seldom write programs entirely from scratch.  When possible, they 
modify older programs to serve new purposes.  When they cannot make use 
of entire old programs, they still copy pieces of code that will work 
in their new program.  And when they can't copy code, they at least 
read similar code to find useful patterns to follow.   

Programs built by copying and modifying existing 
code can be not only cheaper but also better than code 
written from scratch.  If the old code has been well tested 
and used for some time, it is probably pretty dependable.  
Perhaps several bugs have been found and fixed.  Perhaps those 
bugs are mistakes we would make again if we started from scratch. 

But copying code has costs and risks.  Useful programs last a long 
time and go through revision after revision.  The main cost of the code
is not in writing it the first time, but in reading and understanding 
and sometimes modifying it over and over and over.  Sloppy copying
without careful consideration and cleanup can raise that cost through 
inappropriate variable names, convoluted logic that accretes complication 
instead of being more thoroughly analyzed and simplified to fit the 
task at hand, and "fossil" logic that made sense in the original 
application but has no purpose in its new context.  Copying without 
due care can create code that works most of the time but sometimes 
fails because the requirements of the new context are only *almost* 
like those of the code from which it was copied.  

We do want to copy useful code from `assembler_phase2.py` 
to create `assembler_phase1.py`.  In particular, 
`assembler_phase2.py` uses somewhat complex regular 
expressions for parsing assembly code.  Regular expressions 
are difficult to write correctly, and especially 
difficult to debug.  We can save a lot of work by using the 
regular expressions in `assembler_phase2.py` as patterns 
for the regular expressions we need in `assembler_phase1.py`, 
and we can reuse some other logic as well. We do not want to do it 
sloppily.  We will have to read the code carefully and adapt 
it appropriately. 

# Assembler Phase I

Assembler Phase I will need to match each line of input using 
regular expressions.  Some lines of assembly code  will already be in the form 
required by Assembler Phase II.   These can be left unaltered 
and simply written to the output.  We can make use of the regular 
expressions already in Assembler Phase II to recognize the 
assembly language instructions that it can handle, and we can 
simplify the processing of those.   We will need to add a couple new 
patterns for the pseudo-instruction `JUMP` and the 
new form for instructions that refer to data in memory, 
and we will need to
add some processing to "resolve" labels, i.e., to determine 
the addresses they correspond to and substitute those addresses
into instructions (`LOAD`, `STORE`, and `JUMP` ) that 
can refer to labels. 

## Start simple! 

Let's start by writing an `assembler_phase1.py` that only 
passes through the instructions that `assembler_phase2.py` 
can already handle.  This will  make a good base for 
us to work from.  Essentially we'll just be 
copying `assembler_phase2.py` 
and cutting away the parts we don't need.  At the same time we can 
be reading and understanding how `assembler_phase2.py` works 
so that we can plan the new functionality. 

We'll begin by reading `assembler_phase2.py` and getting
an overall sense of how it works and what we can reuse.  
We might skim from first to last, but for seeing how the pieces 
fit together we start at the end, with the main program. 

## Assembler phase 2, main program 

As is typical, the main function is called if the file is run 
as a main program, and not otherwise.  However, this looks
slightly different than others we have seen:  The command line
interface is not called directly from main.   Instead, it is
called before main, and command line arguments are passed to 
main.  

```python
if __name__ == "__main__":
    args = cli()
    main(args.sourcefile, args.objfile)
```

Why would we do this? Later we may want to put the 
Duck Machine simulator, both phases of the assembler,
and a compiler together into one overall script. We won't
want each part of that chain independently reading and
interpreting the command line.  Instead, we want the "main"
program to be callable by a higher-level "main" program for
the combined script. 

Here's the main function: 

```python
def main(sourcefile: io.IOBase, objfile: io.IOBase):
    """"Assemble a Duck Machine program"""
    lines = sourcefile.readlines()
    object_code = assemble(lines)
    log.debug(f"Object code: \n{object_code}")
    for word in object_code:
        log.debug(f"Instruction word {word}")
        print(word,file=objfile)
```

If we peek inside 
`cli`, even if we are not very familiar with the `argparse`
module we can discern that `sourcefile` will be a file, and 
that it will default to `sys.stdin`.   It appears that the whole 
file is read into a list with `readlines`, and then 
the `assemble` function converts that to a list of `Instruction`
objects, which are printed in a loop at the end of the `main` function. 

For our phase 1 of the assembler, we will not be converting 
the lines to machine instructions, but we should be able to 
reuse most of this basic structure.  We can read all the lines 
into a list and then process them as `main` does.  It appears 
that all the interesting work is in the `assemble` function, 
so that's where we'll look next. 

## Assembler phase 2, assemble

From reading `main` we have an expectation that `assemble` 
takes a list of source lines (strings) and returns a list of 
`Instruction` objects.  The header docstrng elaborates: 

```python
 def assemble(lines: list[str]) -> list[int]:
    """
    Simple one-pass translation of assembly language
    source code into instructions.  Empty lines and lines
    with only labels and comments are skipped.
    Handles *only* numerical offsets, not symbolic labels.
    For example:
        STORE   r1,r0,r15[8]    # OK, store value of r1 at location pc+8
        ADD/Z   r15,r0,r0[-3]   # OK, jump 3 steps back if zero is in condition code
    but not
        STORE   r1,variable     # cannot use symbolic address of variable
        JUMP/Z  again           # cannot use pseudo-instruction JUMP or symbolic label 'again'
    """
```

From this docstring can see what `assemble` does do (translate 
instructions like the two positive examples) as well as some of 
what we'll need to do in phase 1 (convert lines like the 
two negative examples into lines like the two positive examples). 

Let's take a look at how `assemble` works, again with an eye 
to what we can reuse and what we will need to modify. 

```python
    error_count = 0
    instructions = [ ]
    for lnum in range(len(lines)):
        line = lines[lnum]
        log.debug(f"Processing line {lnum}: {line}")
        try: 
            fields = parse_line(line)
            if fields["kind"] == AsmSrcKind.FULL:
                log.debug("Constructing instruction")
                fill_defaults(fields)
                instr = instruction_from_dict(fields)
                word = instr.encode()
                instructions.append(word)
            elif fields["kind"] == AsmSrcKind.DATA:
                word = value_parse(fields["value"])
                instructions.append(word)
            else:
                log.debug(f"No instruction on line {lnum}: {line}")
        except SyntaxError as e:
            error_count += 1
            print(f"Syntax error in line {lnum}: {line}", file=sys.stderr)
        except KeyError as e:
            error_count += 1
            print(f"Unknown word in line {lnum}: {e}", file=sys.stderr)
        except Exception as e:
            error_count += 1
            print(f"Exception encountered in line {lnum}: {e}", file=sys.stderr)
        if error_count > ERROR_LIMIT:
            print("Too many errors; abandoning", file=sys.stderr)
            sys.exit(1)
    return instructions
```
    
This is a bit to take in all at once.  We need to summarize and 
abstract away some detail, then focus on the relevant details 
one by one.  

First, let's consider the overall looping structure, abstracting away
what each iteration of the loop does.  

```python
    error_count = 0
    instructions = [ ]
    for lnum in range(len(lines)):
        line = lines[lnum]
        # Do something with line
    return instructions        
```

We can see that it initializes a counter before the loop, and 
the name `error_count` suggests that we might encounter 
lines that we can't translate properly.   We can guess that it is 
appending `Instruction` objects to the `instructions` list, 
which it returns at the end of the function. 

We might have expected the loop to be 

```python
for line in lines: 
```

but instead it is 

```python
    for lnum in range(len(lines)):
        line = lines[lnum]
```

Why?  It seems there must be some need for `lnum`, the
index of the line, within the loop.   If we search for uses of 
`lnum` within the loop body, we get the answer: 

```python
        except SyntaxError as e:
            error_count += 1
            print(f"Syntax error in line {lnum}: {line}", file=sys.stderr)
```

The line number is not used in the translation process per se.  It 
is used to provide error messages.  We're used to seeing error 
messsages from Python that indicate the line number on which the 
error was discovered; our assembler must do the same.   This also suggests 
something about the program we will write:  If we want these line
numbers to be accurate in error messages, we should try to maintain
the same line numbering from phase 1 to phase 2.  This means that, 
for example, we should copy comments from the input to the output
instead of omitting them. 

We can see that the whole body of the loop, after obtaining the 
text of a source line, is wrapped in a try/except block: 

```python
       try: 
            fields = parse_line(line)
            # Process the 'fields' object 
        except SyntaxError as e:
            # etc ... cases for different errors 
            # we might encounter
```

We will need to look in more detail at both the `parse_line` 
function and the processing here in the `assemble` function. 
It's good to finish summarizing the `assemble` function first,
before we dive into another function, but we need to understand a 
little bit more about what `fields` is, so we briefly look 
at the header and docstring of `parse_line`: 

```python
def parse_line(line: str) -> dict:
    """Parse one line of assembly code.
    Returns a dict containing the matched fields,
    some of which may be empty.  Raises SyntaxError
    if the line does not match assembly language
    syntax. Sets the 'kind' field to indicate
    which of the patterns was matched.
    """
```

This gives us what we need to know to make sense of the 
rest of the `assemble` function.  We are expecting a 
`dict` containing information about *fields* in a 
matched instruction.  The `kind` field will identify 
the pattern matched by the line.  So let's look at how 
the `kind` field is used in `assemble`. 

```python
           fields = parse_line(line)
            if fields["kind"] == AsmSrcKind.FULL:
                log.debug("Constructing instruction")
                fill_defaults(fields)
                instr = instruction_from_dict(fields)
                word = instr.encode()
                instructions.append(word)
            elif fields["kind"] == AsmSrcKind.DATA:
                word = value_parse(fields["value"])
                instructions.append(word)
            else:
                log.debug("No instruction on line")
```

We can see that `kind` is a value of the 
`AsmSrcKind` class, and looking for `AsmSrcKind` 
earlier in the file 
we can learn that it is an enumeration: 

```python
class AsmSrcKind(Enum):
    """Distinguish which kind of assembly language instruction
    we have matched.  Each element of the enum corresponds to
    one of the regular expressions below.
    """
    # Blank or just a comment, optionally
    # with a label
    COMMENT = auto()
    # Fully specified  (all addresses resolved)
    FULL = auto()
    # A data location, not an instruction
    DATA = auto()
```

We can see that there are three kinds of source lines that 
`assemble` expects to encounter: comments (which it skips), 
and data and 'full' lines. 

Data words are apparently translated by `value_parse`:

```python
            elif fields["kind"] == AsmSrcKind.DATA:
                word = value_parse(fields["value"])
                instructions.append(word)
```

We can peek at the header of `value_parse` to see what it does. 

```python
def value_parse(int_literal: str) -> int:
    """Parse an integer literal that could look like
    42 or like 0x2a
    """
```

So it just deals with integer literals in either base 10 or base 16. 
We probably won't have to deal with this at all in phase 1 of the 
assembler, except that our input patterns should permit both. 

That leaves the 'full' kind: 

```python
            if fields["kind"] == AsmSrcKind.FULL:
                log.debug("Constructing instruction")
                fill_defaults(fields)
                instr = instruction_from_dict(fields)
                word = instr.encode()
                instructions.append(word)
```

We can see that it ends by encoding the instruction into an integer 
and appending it to the list of instructions. (We can guess that the `instructions`
list is a list of integers rather than `Instruction` objects because 
it contains not only real instructions but also data.)  Working backward 
through the code, we can see that the `Instruction` object is 
constructed by `instruction_from_dict`, which we might 
reasonably surmise takes a `dict` and returns an `Instruction.` 
Peeking at the header for `instruction_from_dict` confirms this: 

```python
def instruction_from_dict(d: dict) -> Instruction:
    """Use fields of d to create an Instruction object.
    Raises key_error if a needed field is missing or
    misspelled (e.g., reg10 instead of r10)
    """
```

The details of `instruction_from_dict` will probably 
not concern us unless we find that for some reason we need to 
create actual `Instruction` objects in phase 1.  More likely 
we will just manipulate strings. 

Still working backward through the code of ```assemble```, 
we see that before passing the `fields` dictionary to `instruction_from_dict`, 
`assemble` passes it to `fill_defaults`.  We can make a 
pretty good guess what that might do, but let's just take a look 
at the header of `fill_defaults` to be sure. 

```python
def fill_defaults(fields: dict) -> None:
    """Fill in default values for optional fields of instruction"""
    for key, value in INSTR_DEFAULTS:
        if fields[key] == None:
            fields[key] = value
```

The header docstring confirms that it fills in missing fields
with default values.  The code of the method is very short, and 
tells us that the code of `fill_defaults` doesn't actually 
have any notion of what fields may be missing and how they 
should be filled in.  This is *table driven* code, with the 
 actual details kept in a table 
(Python dict) ```INSTR_DEFAULTS```: 

```python
# Defaults for values that ASM_FULL_PAT makes optional
INSTR_DEFAULTS = [ ('predicate', 'ALWAYS'), ('offset', '0') ]
```

We can see that 

``` 
    ADD  r1,r2,r3
```

will be treated as 

``` 
    ADD/ALWAYS  r1,r2,r3[0]
```

If we need some defaults in phase 1 of the assembler, we could 
use the same approach. 

Now we've got a pretty good sense of how ```assemble``` 
processes the fields of an instruction, represented as a dict, 
or a data value.  That leaves how it gets those dicts in the 
first place. 

## How Assembler Phase 1 Parses Assembly Language

At the very beginning of ```assemble``` we find the line 

```python
          fields = parse_line(line)
```

We understand now what `fields` should be, and we 
already looked at its header and saw that it parses a 
single line of assembly language, which could be just a 
comment, or the representation of some data, or a
complete  
assembly language instruction (possibly with a couple of 
elisions that `fill_defaults` will fill in). 
We'll need to parse assembly language as well, so we need to 
dive into `parse_line` to see how it works. 

```python
def parse_line(line: str) -> dict:
    """Parse one line of assembly code.
    Returns a dict containing the matched fields,
    some of which may be empty.  Raises SyntaxError
    if the line does not match assembly language
    syntax. Sets the 'kind' field to indicate
    which of the patterns was matched.
    """
    log.debug(f"\nParsing assembler line: '{line}'")
    # Try each kind of pattern
    for pattern, kind in PATTERNS:
        match = pattern.fullmatch(line)
        if match:
            fields = match.groupdict()
            fields["kind"] = kind
            log.debug(f"Extracted fields {fields}")
            return fields
    raise SyntaxError(f"Assembler syntax error in {line}")
```

There are no specific patterns for the assembly language here ... 
it's table-driven code again.   We can summarize `parse_line`
as 

``` 
   for each pattern a source line could match: 
       try matching that pattern.  
       If the line matches that pattern,  
          extract the needed information and return that as a dict.
   otherwise no pattern matched, 
       so raise a syntax error
```

So the real guts of this is going to be a table that contains the 
patterns.  Let's look: 

```python
PATTERNS = [(ASM_FULL_PAT, AsmSrcKind.FULL),
            (ASM_DATA_PAT, AsmSrcKind.DATA),
            (ASM_COMMENT_PAT, AsmSrcKind.COMMENT)
            ]
```

This matches our expectation (each pattern is paired 
with one of the `AsmSrcKind` values), but we need to look 
a little farther to see what the patterns actually look like. 
And that's because they are fairly complex.  Let's start with the 
simplest: 

```python
# Lines that contain only a comment (and possibly a label).
# This includes blank lines and labels on a line by themselves.
#
ASM_COMMENT_PAT = re.compile(r"""
   \s* 
   # Optional label 
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   \s*
   # Optional comment follows # or ; 
   (
     (?P<comment>[\#;].*)
   )?       
   \s*$             
   """, re.VERBOSE)
```

This pattern is wrapped in 

```python
re.compile(r"""
   # the actual pattern goes here           
   """, re.VERBOSE)
```

So it is a regular expression that uses the ```re```
module, which is imported at the head of this source file. 
It is expressed as a 'raw' string so that for example
```r"\n"```  is two characters rather than a single 
newline character, and ```re.compile``` is given the 
```re.VERBOSE``` option so that the pattern can contain 
spaces and comments that are not part of the pattern itself. 

Here is the pattern itself, expressed as a regular expression: 

```python
   \s* 
   # Optional label 
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   \s*
   # Optional comment follows # or ; 
   (
     (?P<comment>[\#;].*)
   )?       
   \s*$             
```

### Comment lines 

We can read it part by part.  It starts with optional 
whitespace (spaces or tabs), and then 

```python
   (
     (?P<label> [a-zA-Z]\w*):
   )?
```

The outer `( ... )?` says this part is optional.  The 
inner part `(?P<label> ... )` says that if it is 
matched, the part within the inner parentheses will be 
in the "group" called `label`.  
`parse_line` will use the `groupdict` method 
to obtain a dictionary describing the match, so 
`label` would be a key in this dictionary if
it matches. 
Note a colon (":")
is required to match, but it is outside the group that 
will be called `label`.  

The text matched as a label must match `[a-zA-Z]\w*`.  
If we look up `\w` in the documentation at 
https://docs.python.org/3/library/re.html, we will see that 
`\w` matches any "word" character, which is described as
"*most characters that can be part of a word in any language, as well as numbers and the underscore*
".  So a label must start with a label, but then it can contain
digits, underscore, and most "letters" 
from any language.  cis_211_不錯 would be a legal label. 

Zero or more spaces may follow the label: 

```python
   \s*
```

and then 

```python
   # Optional comment follows # or ; 
   (
     (?P<comment>[\#;].*)
   )?       
```

Again we have an optional part.  The inner group, which will be 
labeled ```comment```, starts with a character class: 

```python
[\#;]
```

This class matches only two characters, the hash `#` or 
semicolon `;`.    The `.*` then matches anything at 
all, so this pattern will gobble up the rest of the source line. 

Since the comment is optional, the pattern must also match 
spaces that could appear at the end of the line.  The end of the 
line itself matches `$`. 

```python
\s*$
```

Putting these together, both the label and the comment 
are optional, so this pattern matches an empty line, 
a line with just a label, a line with just a comment, 
or a line with both a comment and a label.  This pattern 
will be important to us in phase 1, because we'll need to 
determine the address that each label represents. 

### Data lines 

Next we can look at `ASM_DATA_PAT`.  

```python
# A data word in memory; not a Duck Machine instruction
#
ASM_DATA_PAT = re.compile(r""" 
   \s* 
   # Optional label 
   (
     (?P<label> [a-zA-Z]\w*):
   )?
   # The instruction proper  
   \s*
    (?P<opcode>    DATA)           # Opcode
   # Optional data value
   \s*
   (?P<value>  (0x[a-fA-F0-9]+)
             | ([0-9]+))?
    # Optional comment follows # or ; 
   (
     \s*
     (?P<comment>[\#;].*)
   )?       
   \s*$             
   """, re.VERBOSE)
```

The label part of this pattern is just like the label 
that can be on a comment line.  The remainder matches the 
string `DATA` optionally followed by a value that can be 
either hexadecimal (`0x[a-fA-F0-9]+`) or decimal 
(`([0-9]+)`).   The value part can be followed by a 
comment, which has a pattern similar to that the comment 
pattern we saw above. 

In `assembler_phase1.py` we  can simply pass these `DATA` instructions through 
without change, as we will with comments, but again 
we will need to determine the address associated with the label. 

### The ASM_FULL_PAT pattern 

Deep breath.  We're ready to tackle the big one, 
the pattern for full assembly language instructions. 
Moreover, while we can probably use the other two patterns 
just as they are, we'll need to construct variations 
on `ASM_FULL_PAT` to match source lines that are not
accepted by phase 2 of the assembler.  We need to 
understand this pattern in detail. 

```python
# Instructions with fully specified fields. We can generate
# code directly from these. 
ASM_FULL_PAT = re.compile(r"""
   \s* 
   # Optional label 
   (
     (?P<label> [a-zA-Z]\w*):
   )?
    \s*
    # The instruction proper 
    (?P<opcode>    [a-zA-Z]+)           # Opcode
    (/ (?P<predicate> [a-zA-Z]+) )?   # Predicate (optional)
    \s+
    (?P<target>    r[0-9]+),            # Target register
    (?P<src1>      r[0-9]+),            # Source register 1
    (?P<src2>      r[0-9]+)             # Source register 2
    (\[ (?P<offset>[-]?[0-9]+) \])?     # Offset (optional)
   # Optional comment follows # or ; 
   (
     \s*
     (?P<comment>[\#;].*)
   )?       
   \s*$             
   """, re.VERBOSE)
```

At the beginning and end we have an optional label and an 
optional comment, as before.  In the middle we find the 
instruction itself: 

```
    # The instruction proper 
    (?P<opcode>    [a-zA-Z]+)           # Opcode
    (/ (?P<predicate> [A-Z]+) )?   # Predicate (optional)
    \s+
    (?P<target>    r[0-9]+),            # Target register
    (?P<src1>      r[0-9]+),            # Source register 1
    (?P<src2>      r[0-9]+)             # Source register 2
    (\[ (?P<offset>[-]?[0-9]+) \])?     # Offset (optional)
```

The `opcode` part is simple:  It's just a string of one or 
more letters.  We don't make any attempt to distinguish between 
legal operation codes like "ADD" and misspelled operation codes 
like "add" or "BAMBOOZLE".  

The operation code is followed by a predicate, which is optional: 

```python
    (/ (?P<predicate> [a-zA-Z]+) )?   # Predicate (optional)
```

If the slash is present, at least one letter must follow it.  Again we 
make no attempt to distinguish between legal predicates like "PZ"
and "ALWAYS" and illegal predicates like "IFTHEMOONISFULL". We've 
already seen how `fill_defaults` will substitute "ALWAYS"
if this field is omitted. 

At least one space ("\s+") separates the operation code from the 
remainder of the instruction. 

Each of the three register fields (target, src1, and src2) match 
the pattern "r[0-9]+", which will also match "r999876".  (Are you 
seeing a pattern regarding how much error checking we do in the 
regular expression matching?)  

Finally, the offset field is also optional.  If present it is 
enclosed in square brackets.  "[321]" and "[-321]" are legal, but 
"[+321]" will not match. 

### How these fields are matched 

It's worth reviewing how these regular expressions are
matched before we start sketching `assembler_pass1.py`. 
There are three patterns, each of which permits an optional 
label at the beginning and an optional comment at the end. 
The main `parse_line` function simply tries each pattern 
in the order they appear in the `PATTERNS` list.  It 
extracts a dictionary containing the matching fields, and 
it adds to that dictionary one extra field caled `kind`, 
indicating which pattern matched.  

We can mostly adopt this same strategy.  We won't have to 
encode the instructions and data values as `assembler_phase2`
does, but we will have to process labels, on every kind 
of source line they may appear on.  We may also need 
new patterns for the JUMP pseudo-instruction we introduce 
and for other instructions that refer to labels. 

# Planning assembler_phase1.py

In general outline, we need to do the following: 

* Associate labels with addresses.
* If a statement *refers to* a label (e.g., stores 
into a data location called *x*, or jumps to a label 
called *again*), we will replace that reference with
a combination of register and offset that gives 
the address.  (In particular, we will make addresses 
relative to the program counter.)
* We will translate some pseudo-operations like JUMP 
into real operations like ADD. 
* We will produce one line of output for each line of input. 
If we don't change a line, we will just copy it unchanged. 
If we do change a line, the modified line will replace the
original line. 

## How to get started

The parts of the work are rather interdependent. 
In particular, substituting addresses for labels 
depends on determining what address each label 
represents, and often we will be making that substitution 
as we translate a pseudo-instruction like JUMP into 
a real instruction like ADD.  Moreover, there is a fair 
amount of other functionality like reading each line 
of the source and writing each line after.  We 
might be able to write some simple unit tests for 
individual functions, but we need a way to test
the overall program flow as well.  

We need a plan for incremental development, not just 
of individual functions but of the program as a whole, 
including large parts of `assembler_phase2` that 
we can reuse.  Here's a plan: 

* Write a "stub" version reusing as much of the phase 2 assembler
as possible. The stub will do no translation at all.  Instead of 
adding code to an empty file, we'll start by subtracting code from 
a copy of the phase 2 assembler.  We'll strip away the parts we 
can't reuse before we start adding in new parts. 

* Then we can add code for associating addresses with 
labels.  We won't have anything else to do with
those addresses at first, but we'll be able to write
unit tests for them. 

* Then we'll start adding in the translations.  We can start
with `LOAD` and `STORE` instructions with references
to labeled data locations. 

* We can continue to add patterns for other pseudo-instructions 
and variations that require them until we have everything. 

At each stage we should be producing legal assembly languge 
programs that can be further processed by the phase 2 assembler. 

*Aside:  My initial plan was in a slightly different order, e.g.,
I intended to transform JUMP first and then LOAD and STORE. 
My plan evolved as I worked.  As usual, I am trying to balance 
conveying a realistic work plan with trying not to bog you down 
with every detail, dead end, and change of direction that 
inevitably occurs in software development.*

## The Big Copy

We start by simply copying `assembler_phase2.py` to a new file 
`assembler_phase1.py`.   Then we're ready to start editing. 

First let's fix up the header comment: 

```python
"""
Assembler Phase I for Duck Machine assembly language.

This assembler produces fully resolved instructions,
which may be the input of assembler_phase2.py. 
The input of this phase may contain symbolic 
addresses, e.g., 
    again:   LOAD  r1,x
             SUB  r1,r0,r2[5]
             JUMP/P  again
    x:  DATA 12

Assembly instruction format with all options is 

label: instruction

Both parts are optional:  A label may appear without 
an instruction, and an instruction may appear without 
a label. 

A label is at least one alphabetic letter 
followed by any number of letters (of any kind)
and underscore, e.g., My_dog_boo.

An instruction has the following form: 

  opcode/predicate  target,src1,src2[disp]

Opcode is required, and should be one of the DM2022 
instruction codes (ADD, MOVE, etc).

/predicate is optional.  If present, it should be some 
combination of M,Z,P, or V e.g., /NP would be "execute if 
not zero".  If /predicate is not given, it is interpreted 
as /ALWAYS, which is an alias for /MZPV. 

target, src1, and src2 are register numbers (r0,r1, ... r15)  

[disp] is optional.  If present, it is a 10 bit 
signed integer displacement.  If absent, it is 
treated as [0]. 

The second source register and displacement may be replaced
by a label, e.g., 
    LOAD  r1,x
In an instruction with the pseudo-operation JUMP, 
all the registers may be omitted (a target of r15 is implied)
and replaced by a label, e.g., 
    JUMP/Z  again
Instructions with these forms will be translated to fully
resolved instructions, e.g., 
    LOAD r1,r0,r15[14]  #x
    ADD/Z r15,r0,15[-7] #again

DATA is a pseudo-operation:
   myvar:  DATA   18
indicates that the integer value 18
should be stored at this location, rather than
a Duck Machine instruction.

"""
```

We can keep the import statements, 
including the log configuration.  We can add other 
import statements later if we need them, and at the
end we can trim out any we didn't use.  (PyCharm 
helpfully greys out imports that aren't used, but it 
is confused about the `context` import that we use 
to link together different parts of this multi-week 
project.)

The `SyntaxError` exception is still useful.  The limit 
of 5 errors before we give up is still fine. 

It's not obvious whether we'll still want `DICT_NO_MATCH` or not. 
We can cut it later if we don't need it. 

We'll keep the basic approach of the `AsmSrcKind` 
enumeration and the `PATTERNS` table that associates 
regular expression patterns with different kinds of lines.  
We know that soon we'll need to add a pattern or two, but 
not yet.  For now we keep the regular expressions as they are. 
Likewise the defaults table. `parse_line`,  
and `value_parse` can also stay.   

How about `instruction_from_dict`?  This function is 
for producing an `Instruction` object.  We are unlikely 
to want it in this form.  Let's cut it out; we can always copy 
it back from `assembler_phase2.py` if we discover we need it. 
```fill_defaults``` is important when constructing `Instruction`
objects, but will also be unnecessary here. 

The `assemble` function needs a new name and a new 
docstring, and it should return a list of 
strings instead of a list of integers, but we can reuse most of it. 

```python
def transform(lines: list[str]) -> list[int]:
    """
    Transform some assembly language lines, leaving others
    unchanged. 
    Initial version:  No changes to any source line. 
    
    Planned version: 
       again:   STORE r1,x
                SUB   r1,r0,r0[1]
                JUMP/P  again
                HALT r0,r0,r0
       x:       DATA 0
    should become 
       again:   STORE r1,r0,r15[4]   # x
                SUB   r1,r0,r0[1]
                ADD   r15,r0,r15[-2]
                HALT r0,r0,r0
       x:       DATA 0
     """
```

We can leave the loop through the lines as it is, and 
even the pattern matching.  Maybe we should change `instructions`
to `transformed`, to be clear about its purpose.  But mostly 
we are just going to cut out the translation to object code.   Where 
we had 

```python
            if fields["kind"] == AsmSrcKind.FULL:
                fill_defaults(fields)
                instr = instruction_from_dict(fields)
                word = instr.encode()
                instructions.append(word)
```

we can chop it down to 

```python
            if fields["kind"] == AsmSrcKind.FULL:
                log.debug("Passing through FULL instruction")
                transformed.append(line)
```

We will make a similar change to handling of ```DATA``` lines, 
simply adding each line to the ```transformed``` list.  

One place we must add a little code is the handling of comment 
lines.  The phase 2 program discarded these, because no object 
code is generated for a comment.  We want to preserve them. 

```python
            else:
                transformed.append(line)
```

We should fix up the documentation messages in the command line interface, 
but reading one file and writing another is still fine:

```python
def cli() -> object:
    """Get arguments from command line"""
    parser = argparse.ArgumentParser(description="Duck Machine Assembler (phase 1)")
    parser.add_argument("sourcefile", type=argparse.FileType('r'),
                            nargs="?", default=sys.stdin,
                            help="Duck Machine assembly code file")
    parser.add_argument("objfile", type=argparse.FileType('w'),
                            nargs="?", default=sys.stdout, 
                            help="Transformed assembly language file")
    args = parser.parse_args()
    return args
```


At this point we should have a perfectly useless program that reads a fully resolved assembly
language program and prints it without changes.  We can test this 
by running it on a .dasm file from the programs directory: 

```bash
 python3 assembler_phase1.py programs/fact.dasm
```

We will notice one problem:  Since the `lines` list
includes a newline at the end of each string, the 
`transformed` list does also, and this causes our 
output to include extra newlines (a blank line after each 
line of code).  There are several ways we could fix this. 
The approach I chose 
was changing one line in `transform` from 

```python
        line = lines[lnum]
```

to 

```python
        line = lines[lnum].rstrip()
```

### Address resolution

A key part of our goal is to change a line like 

```
    JUMP/PZ    somewhere
```

to a line like 

```
    ADD  r15,r0,r15[-4]
```

where -4 would be the difference between the current 
instruction address and the address at which the 
label `somewhere` is found.  This involves both
analyzing the source code and transforming it.  We 
want to proceed in small steps, and it is not possible 
to perform the transformation (substituting a relative 
address like -4 for the label `somewhere`) without
the analysis step, but it is possible to perform the 
analysis without the transformation, so that is the 
step we'll program first.  

### Two passes 

One thing you may notice right away is that a label 
might be *used* before it is *defined*.  For example, 
consider our `max` program: 

``` 
   LOAD r1,r0,r0[510]     # Trigger read from console
   LOAD r2,r0,r0[510]     # Trigger read from console
   SUB  r0,r1,r2[0]
   JUMP/P r1bigger
   STORE r2,r0,r0[511]    # Trigger write to console
   HALT r0,r0,r0
r1bigger:
   STORE r1,r0,r0[511]    # Trigger write to console
   HALT r0,r0,r0
```

The label `r1bigger` appears in a `JUMP` instruction 
before it appears as a label.  This tells us that a single 
loop through the lines (a single *pass*) will not work.  
We will need one loop to gather information (without 
changing anything), and a second loop to perform the 
transformation.  This approach, in which we loop through 
the same data more than once, is called a *two pass algorithm* 
or more generally a *multi-pass algorithm*. 

_Aside_:  We've seen two-pass algorithms before. 
Recall that the `naked_single` method for our Sudoku solver
made one pass through a group to determine which values were
already used, then a second pass through the same group of 
tiles to remove those values as candidates in unknown tiles. 
The `hidden_single` method made one pass through the tiles in
a group to determine which values were _not_ yet used 
(we called them _leftover_ values),
then for each _leftover_ value it made another pass through
the same tiles to determine whether there was just one
place to put that value.  In each of these cases, we gathered some information in the first pass, then used it in a subsequent pass or passes. 

To implement address resolution as a two pass algorithm, 
instead of modifying the loop body of `transform`, we 
will make a second copy of the loop, in a separate function. 
That function will run exactly the same pattern matching as 
```transform```, but instead of building a new list of 
transformed source lines, it will build a table (a dict)
associating labels with addresses.  

```python
def resolve(lines: list[str]) -> dict[str, int]: 
    """
    Build table associating labels in the source code 
    with addresses. 
    """
```

We know that we are going to be adding a few new patterns, 
but the pattern matching has already been factored into 
a separate ```parse_line``` function, so we won't have to 
duplicate much.  We'll start by just copying the whole 
body of ```transform``` into ```resolve```, and then 
make our modifications. 

```python
    error_count = 0
    transformed = [ ]
    for lnum in range(len(lines)):
        line = lines[lnum].rstrip()
        log.debug(f"Processing line {lnum}: {line}")
        try: 
            fields = parse_line(line)
            if fields["kind"] == AsmSrcKind.FULL:
                log.debug("Passing through FULL instruction")
                transformed.append(line)
            elif fields["kind"] == AsmSrcKind.DATA:
                transformed.append(line)
            else:
                log.debug(f"No instruction on line {lnum}: {line}")
                transformed.append(line)
        except SyntaxError as e:
            error_count += 1
            print(f"Syntax error in line {lnum}: {line}", file=sys.stderr)
        except KeyError as e:
            error_count += 1
            print(f"Unknown word in line {lnum}: {e}", file=sys.stderr)
        except Exception as e:
            error_count += 1
            print(f"Exception encountered in line {lnum}: {e}", file=sys.stderr)
        if error_count > ERROR_LIMIT:
            print("Too many errors; abandoning", file=sys.stderr)
            sys.exit(1)
    return transformed
```

One of the parts we *don't* want to duplicate is printing 
specific error messages for each kind of error we might 
find in the source assembly code.  We don't want two messages 
for each error!  So we need to decide: Handle syntax errors 
in `resolve`, or in `transform`, or some in each? 

One kind of error we could encounter is a label that is used 
but never defined  (probably because it is misspelled).  That 
will be easier to deal with in `transform`, because in 
`resolve` we don't know the difference between a label that
is not defined at all and a label that just hasn't been 
defined *yet*.  Since we will handle at least some errors in 
`transform`, we'll take the tactic of handling all of 
them there.  In `resolve` we'll still need to catch 
exceptions, but we can just ignore them.  We'll replace the 
long list of exceptions by one very simple handler, but
leave a little logging there in case we need to debug
a program error that causes an unexpected exception: 

```python
        except  Exception as e:
            log.debug(f"Exception encountered line {lnum}: {e}")
            # Just ignore errors here; they will be handled in
            # transform
```

We can also remove the `error_count` variable from 
`resolve`.  Instead of initializing and returning the 
`transformed` list, we'll initialize and return a 
dictionary; let's call it `labels`.  

```python
    labels: dict[str, int] = { }
```

When we encounter a line with  label, we will need to add 
an entry to the table.  The value of that entry should be 
the address corresponding to the label.  To do that, we 
must keep track of addresses.   But an address is not the 
same as the line number, because some lines in the source 
file do not correspond to any code in the object code 
that will be generated by phase 2 of the assembler.  
Therefore we'll need to keep track of the current address, 
which I will creatively call `address`.  Initially 
it is 0, since we start our Duck Machine object code 
programs at address 0 in memory.  
After we process a line that will take up space in the 
object code, we will increment it.  After a line that 
does not appear in the object code, we will not increment
it. 

Which source lines will take up space in the object program? 
In our current set of patterns, lines that do *not* take up 
space match the `ASM_COMMENT_PAT` pattern and are 
tagged with a `kind` of `AsmSrcKind.COMMENT`.  
We will add some patterns later, but we'll try to preserve 
the property that only lines with the `AsmSrcKind.COMMENT`
kind do not take up space in memory.  That will simplify 
our logic:  For `AsmSrcKind.COMMENT` we will not 
increment the address counter, and for any other kind of 
line we will. 

All the patterns so far allow for labels and put them 
in a group called ```label```.  We'll also try to maintain 
that property as we add more patterns. 

With these two properties, the logic of building the 
table is pretty simple.  In pseudocode: 

``` 
labels: dict[str, int] = { }
address = 0
for each line: 
    if the line has a label: 
       add (label, address) to labels
    if the line is not a comment: 
       increment the address
return labels
```

I will leave it to you to write the Python code.  We can 
start a unit test suite to check it.  Once again we will 
place `test_assembler_phase1.py` in the `tests` directory.  

```python
"""Unit tests for assembler phase 1"""

import unittest
from assembler_phase1 import *

class TestResolve(unittest.TestCase):

    def test_sample_resolve(self):
        lines = """
        # comment line at address 0
        
        # Blank line above is also address 0
        start:   # and start should also be address 0
        next:    ADD/P   r0,r1,r2[15]  # Still address 0
                 SUB     r1,r2,r3      # Address 1
        after:   MUL     r1,r2,r3[15]  # Address 2
        finally:  # Address 3
        fini:    DIV     r1,r2,r3      # Address 3
        """.split("\n")
        labels = resolve(lines)
        self.assertEqual(labels["start"], 0)
        self.assertEqual(labels["next"], 0)
        self.assertEqual(labels["after"], 2)
        self.assertEqual(labels["finally"], 3)
        self.assertEqual(labels["fini"], 3)

if __name__ == "__main__":
    unittest.main()
```

## Transform

Our main program could call `resolve` first, and then pass
the table produced by `resolve` to `transform`.  I think it's
a little nicer to keep the main program as simple as possible,
and instead have `transform` call `resolve` to obtain the
table of labels and addresses, so that's how I did it. 

`transform` will need to use 
the table of labels for each line that uses a symbolic 
label in place of an address.  The instructions that need 
to be transformed will either specify one register and a
reference to a label, like 

```
    STORE  r1,x
```

or they will have only a reference to a label, like 

```
    JUMP/Z  again
```

Leaving aside pseudo-operations like `JUMP` for the 
moment, we'll start with existing operation codes like 
`STORE` and `LOAD`. 

We'll need a new pattern for these.  We can base it on 
the existing regular expression `ASM_FULL_PAT`, keeping 
`target` but replacing
`src1`, `src2`, and `offset` by a single 
field `labelref` that is like the optional `label` 
part of the line but not optional and without the trailing 
":".   We'll call it `ASM_MEMOP_PAT`. 
I think you can figure it out. 

We'll need to add our new pattern to the ```PATTERNS``` table. 
First we need to add a corresponding ```AsmSrcKind```
element: 

```python
    # An instruction that refers to a memory
    # location in place of its source and offset
    # parts.
    MEMOP = auto()
```

Then we can add it to the table

```python
PATTERNS = [(ASM_FULL_PAT, AsmSrcKind.FULL),
            (ASM_DATA_PAT, AsmSrcKind.DATA),
            (ASM_COMMENT_PAT, AsmSrcKind.COMMENT),
            (ASM_MEMOP_PAT, AsmSrcKind.MEMOP)
            ]
```

Because of our table-driven design, this should 
be enough for `parse_line` to parse 
lines of this new kind.  We'll add a unit test
to be sure: 

```python
class TestParseMemop(unittest.TestCase):

    def test_parse_memop_unlabeled(self):
        line = "  LOAD/P  r3,something"
        fields = parse_line(line)
        self.assertEqual(fields["kind"], AsmSrcKind.MEMOP)
        self.assertEqual(fields["labelref"], "something")
        self.assertEqual(fields["opcode"], "LOAD")
        self.assertEqual(fields["label"], None)

    def test_parse_memop_labeled(self):
        line = "bogon:  STORE/Z r3,something # comments too"
        fields = parse_line(line)
        self.assertEqual(fields["kind"], AsmSrcKind.MEMOP)
        self.assertEqual(fields["labelref"], "something")
        self.assertEqual(fields["opcode"], "STORE")
        self.assertEqual(fields["label"], "bogon")
```

With this working, we need to apply the transformation 
in `transform`.  Note that we should not have to 
change `resolve` at all, because we have maintained 
the properties that a label, if present, is always in the 
`label` field and every *kind* except 
`AsmSrcKind.COMMENT` takes one memory cell. We just 
need to add a case to `transform` for the new 
*kind*: 

```python
            elif fields["kind"] == AsmSrcKind.MEMOP: 
```

What should we do here?  Rather than copying the line 
directly into ```transformed```, we need to build a new 
line with some copied fields and some new fields.  Let's 
consider each field in turn: 

* label:  If a label was present, we should copy it,
followed by a colon (":").  If a label was not present, 
we don't want to print 'None', so we'll substitute some 
spaces. 

* opcode: We don't need to change this

* predicate:  If a predicate is present, we will copy 
it, preceded by a "/".  If no predicate is present, 
we'll replace ```None``` by an empty string.  

* target register:  No need to change this 

* labelref:  We will replace this with registers 
and an offset. 

* comment:  If present, we should copy this. 
If there is no comment, we'll use an empty string. 
(We will also add a comment of our own with the 
label we have replaced.)

While we could write several different string formats to 
cover the various conditions (label present or not, 
predicate present or not, comment present or not), it is 
much simpler to just update the ```fields``` dict returned 
by ```parse_line```.  For example, to handle the optional 
label we can write 

```python
    if fields["label"] is None: 
       fields["label"] = "    "
    else: 
       fields["label"] = fields["label"] + ":"
```

We can write similar code for the ```predicate``` and 
```comment``` fields.   To avoid cluttering ```transform```, 
we will write a separate function ```fix_optionals```:

```python
def fix_optional_fields(fields: dict[str, str]):
    """Fill in values of optional fields label,
    predicate, and comment, adding the punctuation
    they require.
    """
```

Now I'd like to write some unit test cases for 
```fix_optional_fields```, but I've got a problem: 
I have not specified how many spaces an empty label 
will be replaced by.  I'll have the same problem when 
I actually transform source instructions.  How can 
I write an ```AssertEqual``` if I don't have a clear 
and precise definition of the result? 

Actually the problem is not that I lack a precise 
specification.  The specification is sufficiently 
precise, but it allows some flexibility in 
how much whitespace to include in each 
of the places that some whitespace is needed. 
 I do not want to add unnecessarily 
  strict and arbitrary details for the 
 sake of testing.  Instead, I will 
 write a function that "canonicalizes" strings 
 before comparison. 

### Aside: Equivalence and Canonical Forms

When we want to consider some subsets of 
a set of elements to be all equivalent, it is useful to 
think of them as forming *equivalence classes*
that *partition* the set.  Equivalence 
classes are formed by any relation ~ that is
*reflexive* (A ~ A), *transitive* (A ~ B and B ~ C implies 
A ~ C), and *symmetric* (A ~ B implies B ~ A). We call 
any such relation an *equivalence relation*. 
An equivalence relation *partitions* a set
into *equivalence classes*, meaning 
it divides the set into disjoint subsets of elements 
such that  all the elements in one subset (equivalence 
class) are equivalent to all the other elements in
that equivalence class, and not equivalent to any element
in any other equivalence class.  

Often, but not always, it is convenient to pick one 
element of each equivalence class to serve as a 
representative of that class.  We call it the 
*canonical example* of the class.  If it is easy to 
transform any other element into the canonical example 
of its equivalence class, then the easiest way to check 
whether two elements are equivalent may be to 
transform both of them into canonical form and them 
check whether they are identical.  

"Equal except for leading and trailing whitespace 
and differences in the amount of other whitespace" 
is an example of an equivalence relation that is simplest to 
handle by *canonicalization*.  Rather than directly comparing 
two strings to see whether they are the same except for amount
of whitespace, we can convert both into a canonical form and 
then perform a simple string comparison.  We will take as 
the canonical example of strings in a class a string
in which initial and trailing whitespace has been 
trimmed and all other whitespace sequences have been 
compressed to a single space.  We'll 
create a helper function that performs this canonicalization, 
which we'll call ```squish```.   It's easy with the ```split```
and ```join``` functions: 

```python
def squish(s: str) -> str:
    """Discard initial and final spaces and compress 
    all other runs of whitespace to a single space,
    """
    parts = s.strip().split()
    return " ".join(parts)
```

We'll add this function to our test suite and use it 
to write simple tests for ```fix_optional_fields```. 

```python
class TestOptionalFieldsFixup(unittest.TestCase):

    def test_fill_defaults(self):
        line = "  LOAD   r1,something"
        fields = parse_line(line)
        fix_optional_fields(fields)
        self.assertEqual(squish(fields["label"]), squish(""))
        self.assertEqual(squish(fields["predicate"]), squish(""))
        self.assertEqual(squish(fields["comment"]), squish(""))

    def test_keep_optionals(self):
        line = "lab:  LOAD/P   r1,something # comment"
        fields = parse_line(line)
        fix_optional_fields(fields)
        self.assertEqual(squish(fields["label"]), squish("lab:"))
        self.assertEqual(squish(fields["predicate"]), squish("/P"))
        self.assertEqual(squish(fields["comment"]), squish("# comment"))
```

That might seem like a lot of work just to test these fields, 
but we'll use ```squish``` again for comparing whole lines. 

### PC-Relative Addresses

We would have enough information now to transform a ```MemOp```
instruction, if we were content to just use the address 
as it appears in the table returned by ```resolve```.  However, 
I would prefer to use addresses that are relative to the 
program counter.  For example, instead of "Jump to address 12", 
I prefer "Jump forward 3 instructions" or "Jump backward 4 instructions", 
and I similarly prefer a PC-relative address for variables. 
Instead of "Load from address 15", I want "Load from 
the address 12 words forward from here". 
Using *relative* addresses makes the object code *relocatable*: 
While we are starting all of our programs at address 0, 
relocatable object code would work exactly the same if we moved
the whole program to a different starting address. 

To make PC-relative addresses, we need one more 
piece of information:  The current address. 
We've already calculated this in the ```resolve``` function; we 
could either save the address values there, or calculate them 
again in the same way.  Let's just calculate them again. 

We could add a line to increment the address in each case 
*except* the comment line case.  But then, we would need to 
remember to do it for each additional case we add. Since we 
are preserving the property that *lines with kind 
```AsmSrcKind.COMMENT``` are the only lines that do not 
take up memory*.  Instead of adding an increment to each 
of the cases that do need it, it will be simpler and 
more robust to add a separate check after handling 
all the cases.  The outline of the loop logic will 
be: 

``` 
   transformed = [ ]
   address = 0
   for each line: 
       parse the line
       if kind is __ : 
           handle that case
       elif kind is ___ : 
           handle that case
       etc
       # Separate case analysis for incrementing address
       if kind != AsmSrcKind.COMMENT:
           increment address
   return transformed
```

Now with the table of memory addresses and a variable 
holding the address of the current instruction, we have 
everything we need to compute a PC-relative address.  

```python
                ref = fields["labelref"]
                mem_addr = labels[ref]
                pc_relative = mem_addr - address
```

If we call ```fix_optional_fields``` to provide the 
actual text for all the instruction fields, all that is 
left is to format the fields as a full assembly 
language instruction.  For the first source register, 
we'll use use "r0".  For the second source register, 
we'll use "r15", and we'll use the value of ```pc_relative```
for the offset.  

It took me several rounds of debugging to get the details 
of the transformed instruction right.  There is nothing 
conceptually difficult about it, but there are lots of 
details that provide opportunities for error, and I never 
miss such an opportunity.  To make the format string a little 
less unwieldy I created a short alias for the ```fields```
variable: 

```python
                f = fields
```

Nonetheless the format string is a monster: 

```python
                full = (f"{f['label']}   {f['opcode']}{f['predicate']} " +
                    f" {f['target']},r0,r15[{pc_relative}] #{ref} " +
                    f" {f['comment']}")
```

Note the ```#{ref}``` following the operands.  The translation 
would work without this (and without preserving comments), but 
including it makes it easier for an assembly language programmer
to debug their code. 

We use the ```squish``` function
again to create a test case that 
allows differences in spacing.

```python
class TestTransformation(unittest.TestCase):

    def test_memop_no_optional(self):
        lines = """
        # A comment line
        at_zero: ADD r0,r0,r0 
        LOAD  r5,later
        STORE r5,at_zero
        ADD  r5,r0,r0[42]
        HALT r0,r0,r0
        later: DATA 84
        """.split("\n")
        transformed = transform(lines)
        expected = """
        # A comment line
        at_zero: ADD r0,r0,r0 
        LOAD  r5,r0,r15[4] #later
        STORE r5,r0,r15[-2] #at_zero
        ADD  r5,r0,r0[42]
        HALT r0,r0,r0
        later: DATA 84
        """.split("\n")
        self.assertEqual(len(transformed),len(expected))
        for i in range(len(expected)):
            self.assertEqual(squish(transformed[i]),squish(expected[i]))

    def test_memop_preserve_optionals(self):
        lines = """
        # Just a comment
        zero: # With a comment 
        
        # Blank line above should appear in output
        still_zero:  ADD  r5,more      # Another comment
        now_one:     LOAD r5,zero      # Why not? 
        now_two:     STORE/M r5,somewhere # Silly but it's just a test
        somewhere:   HALT r0,r0,r0  # We would clobber this instruction!
        more:        DATA 17
        """.split("\n")
        transformed = transform(lines)
        expected = """
        # Just a comment
        zero: # With a comment 
        
        # Blank line above should appear in output
        still_zero:  ADD  r5,r0,r15[4] #more # Another comment
        now_one:     LOAD r5,r0,r15[-1] #zero # Why not? 
        now_two:     STORE/M r5,r0,r15[1] #somewhere # Silly but it's just a test
        somewhere:   HALT r0,r0,r0  # We would clobber this instruction!
        more:        DATA 17
        """.split("\n")
        self.assertEqual(len(transformed), len(expected))
        for i in range(len(expected)):
            self.assertEqual(squish(transformed[i]), squish(expected[i]))
```

## Adding JUMP instructions

So far we have made provision for instructions that provide 
a target register and a memory address.  This isn't quite 
what we need for a JUMP pseudo-instruction, which has r15 
as an implicit target register.  Recall that one of our 
motivating examples was 

``` 
   LOAD r1,r0,r0[510]     # Trigger read from console
   LOAD r2,r0,r0[510]     # Trigger read from console
   SUB  r0,r1,r2[0]
   JUMP/P r1bigger
   STORE r2,r0,r0[511]    # Trigger write to console
   HALT r0,r0,r0
r1bigger:
   STORE r1,r0,r0[511]    # Trigger write to console
   HALT r0,r0,r0
```

We want to transform that JUMP instruction into 

```
   ADD/P r15,r0,r15[3] #r1bigger
```

I leave that to you.  The main steps you will need are: 

* Create a new pattern to recognize an instruction 
  with just one operand, a memory address.  Since 
  we will use this *only* for the JUMP pseudo-operation, 
  I suggest replacing the operation code part of the 
  pattern with the literal string "JUMP".
  
* Create a new AsmSrcKind element to associate with 
  the new pattern.  I called mine ```JUMP```. 
  
* Associate the new pattern with the new AsmSrcKind 
  element in the ```PATTERNS``` table.
  
* Add a new case in ```transform``` for creating the 
  corresponding ```ADD``` instruction and appending 
  it to the list of transformed instructions. 
  
  
Here are test cases to check your work: 

```python
    def test_jump_example(self):
        """This is the example from the header docstring of transform"""
        lines = """
        again: STORE r1,x
               SUB r1,r0,r0[1]
               JUMP/P  again
               HALT  r0,r0,r0
        x: DATA  0
        """.split('\n')
        transformed = transform(lines)
        expected = """
        again:  STORE r1,r0,r15[4]   #x
                SUB   r1,r0,r0[1]
                ADD/P r15,r0,r15[-2] #again
                HALT r0,r0,r0
        x:      DATA 0
        """.split('\n')
        self.assertEqual(len(transformed), len(expected))
        for i in range(len(expected)):
            self.assertEqual(squish(transformed[i]), squish(expected[i]))

    def test_jump_around(self):
        """Just a sample loop with an early exit"""
        lines = """
        begin: LOAD  r1,x
        loop:  SUB r1,r1,r0[1]
               JUMP/Z endloop
               STORE r1,r0,r0[511]  # print it
               JUMP loop
        endloop: 
                HALT  r0,r0,r0
        x:      DATA 42
        """.split("\n")
        transformed = transform(lines)
        expected = """
        begin: LOAD  r1,r0,r15[6] #x
        loop:  SUB r1,r1,r0[1]
               ADD/Z  r15,r0,r15[3] #endloop
               STORE r1,r0,r0[511]  # print it
               ADD r15,r0,r15[-3] #loop
        endloop: 
                HALT  r0,r0,r0
        x:      DATA 42
        """.split("\n")
        self.assertEqual(len(transformed), len(expected))
        for i in range(len(expected)):
            self.assertEqual(squish(transformed[i]), squish(expected[i]))
```

This completes the required features of your `assembler_phase1`.

# Postscript

## Assemble and Go

In some past versions of this project series, it was tedious
to chain together the different parts:  Running phase 1 of
the assembler, then running phase 2 of the assembler, then
executing the resulting object code.  The commands for these
steps differed enough between Unixes (Linux and MacOS) and Windows
that it was also confusing.  Why not have a single Python
program that does all the steps?   

You can find that single Python program in `run/asmgo.py`.
The explicit path manipulation in `context.py` in each
directory still bothers me, but this is the payoff: 
We can now run each program separately, or run them
as one combined program.  This is also why the `main`
functions in each have been refactored, so the 
the one combined program can take care of the
command line interface.  We will do the same thing again
in the next project, when we build a compiler that
produces Duck Machine assembly code. 

## Bells and Whistles

All the required features for this project are 
described above. 
There are many more useful features we could add, including: 

* A "load address" pseudo-instruction, which could have 
the opertion code "LDA".  Whereas "LOAD r1,x" moves the 
value of a memory cell into register 1, "LDA r1,x" would 
move the address of that memory cell into register 1. 

* An extension to the `DATA` pseudo-op to support a 
list of data elements.  Together with the LDA pseudo-op, 
this would be useful for writing loops that iterate through 
a sequence of values starting at a named location.  

* Permitting operation codes to be spelled in lower-case or 
mixed case, replacing them by the upper-case spelling 
required by phase 2 of the assembler. 

* The combined `asmgo` script runs each step, regardless
  of whether the prior step succeeded or failed.  It would be
  better if each `main` function returned an indication of
  whether that step was successful, with no errors, or whether
  some error (e.g., a syntax error in the assembly language
  input) was detected.  The `asmgo` script would then run
  only until it _either_ finished all the steps _or_ 
  received notification that some step had failed. 
  
None of these are required, but you may wish to at least think 
about how you would implement them. 


## Context: Assembly Language Programming

Few programmers today write much assembly code, but a few do, 
often in small quantities to handle some low-level hardware 
interface, or a small but critical part of the operating system. 
If you do find yourself writing assembly code professionally, 
you will probably use a `macro assembler` which not only 
translates labels to addresses as we have done here, but also 
allows you to write your own custom transformations in the 
form of *macros*.  A macro is something like a function, but 
instead of *doing* something, it *becomes* something, i.e., 
a macro-assembler substitutes the textual result of calling a macro 
for the macro call. 

You are more likely to *read* assembly code than to *write* it. 
Someday you will be writing code in C or C++ or, just as likely, 
a programming language X that hasn't been invented yet, and you 
will wonder "why is this running slowly?".  You may wish to 
know what your code in language X is translated into by your 
compiler.  Most compilers will tell you if you ask nicely.  For 
example, here is a simple function in the C language (which you 
can look forward to learning in CIS 212): 

```C11
int add(int x, int y) {
    int result = x + y;
    return result;
}
```

Here is the Intel X86 assembly language produced by the C 
compiler on my laptop.  I obtained it by giving the -S 
command-line option to the compiler. 

```
_add:                                   ## @add
	.cfi_startproc
## BB#0:
	pushq	%rbp
Lcfi0:
	.cfi_def_cfa_offset 16
Lcfi1:
	.cfi_offset %rbp, -16
	movq	%rsp, %rbp
Lcfi2:
	.cfi_def_cfa_register %rbp
	movl	%edi, -4(%rbp)
	movl	%esi, -8(%rbp)
	movl	-4(%rbp), %esi
	addl	-8(%rbp), %esi
	movl	%esi, -12(%rbp)
	movl	-12(%rbp), %eax
	popq	%rbp
	retq
	.cfi_endproc
```

It's more complex than Duck Machine assembly language, 
but not that much more.  The x86 registers have names 
like %edi and %esi, but conceptually they are 
similar to Duck Machine registers.  We use PC-relative 
addresses for memory in the Duck Machine; these x86 
instructions use offsets from another register 
(%rbp) dedicated to that purpose.  The biggest differences 
are that the x86 has some special operations for calling and 
returning from functions, and it can load a value from 
memory and add it to a register in a single instruction, 
as it does here in 

```
	addl	-8(%rbp), %esi
```

where `%esi` is the target register and ```-8(%rbp)```
is the memory address (here the offset is -8, so this 
is like `%rbp[-8]` in the notation we have adopted). 

## Two-pass algorithms 

Aside from the regular expressions, which can be a challenge 
to read and write, I have found that for many students the 
most challenging part of this project is the idea of a 
*two-pass* algorithm, which gathers information in one loop
over the data and then uses that information in a second 
loop over the same data.  In this program, the first pass 
is `resolve` and the second pass is the remainder 
of `transform`.   It is very often easier and more 
efficient to solve a problem with a two-pass algorithm 
than with a single "pass" over the data.  I will give you 
several other small examples to solve with two-pass algorithms, 
and you can expect a problem that requires a two-pass 
algorithm on the final exam.

What I often see in place of a simple two-pass algorithm is 
a much more complicated algorithm with nested loops.  For example, 
you could solve the problem of references to labels that appear 
later in the assembly code by searching for each label while
trying transform that reference.  That approach is both more 
complicated and less efficient, often dramatically so.  
For example, suppose instead of a separate loop through the 
lines in the `resolve` function, we could have designed 
the `transform` function something like this: 

``` 
transform(lines) -> instructions: 
    for each line: 
       if it references a label: 
          for each line: 
              if it defines the label: 
                 address = here 
                 break from inner loop
          if we didn't find the address: 
             some kind of error message 
       transform the line into an instruction, 
       using the address we found if needed 
```

This approach, searching for each label individually, 
can take time that is *quadratic* in the length of the 
assembly language program.  The approach we have taken, 
with just one extra pass through the assembly code in 
`resolve`, requires time only linear in the length 
of the assembly language program.  


## Copy-paste as a programming technique

I will not give you an exam problem in reading, understanding, 
and adapting existing code.  I wish I knew how to test that 
skill on an exam and further incent you to practice it, but I don't.  
I believe it is a real and important 
skill. I don't need to convince you to 
copy code, because you will do that in any case, as 
generations of programmers before you have.  What I do want 
to convince you of is the value of developing a 
systematic and disciplined approach to copying and 
modifying code for a new purpose.  

* Carefully read the code you hope to reuse.  It is fine 
    (and often necessary) to skip over parts that are not relevant
    to the new purpose.   Whole functions or classes that will 
    be used without modification might be copied without detailed 
    reading, just as we might use a library function if we know
    *what* it does but not necessarily *how* it does it.  
    But the code we intend to modify must be really understood. 

    Reading and understanding code is a skill in itself. The 
    approach I have tried to convey in this project is one of 
    step-by-step summary.  We don't try to understand all the 
    code at once. We try to understand one part and create
    a brief summary that will suffice in understanding other 
    parts of the code. 
    
* As in all programming, we need to break the task of 
    adaptation into small steps:  Code a little, 
    test a little.  Sometimes this can be 
    a series of small changes to functionality, but often 
    it is worthwhile to break the overall approach down 
    into a phase in which we are just *removing* code that 
    we don't wish to keep followed by a phase in which we 
    *add* and *modify* the new functionality. 
    
* Debugging is always a challenge, but it is especially 
    challenging to debug code that you didn't write.  
    The techniques you use in reading code are applicable 
    also in debugging.  Make predications about the 
    behavior of the code and run experiments to test them, 
    all the time trying to build simple, coherent summaries 
    of each part of the code. 
    
