# Malformed Fixture

This fixture exercises every check_markdown.py check exactly once, in
document order, ending with an unclosed fence so it does not mask the
findings before it.

#NoSpace

####### Too many hashes

    #### Indented heading

	This paragraph line starts with a tab.

This line ends with two trailing spaces.  
The next line is not blank, so the break above is flagged.

- one
- two
* three

See the [style guide][style] for more detail.

| a | b |
| - | - |
| 1 | 2 |

```code`with`backticks
Content inside a properly closed but invalid backtick info string.
```

```python
def f():
    return 1
``
Still inside the code block after the too-short closer, until EOF.
