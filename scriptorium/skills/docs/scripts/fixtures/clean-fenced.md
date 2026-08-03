# Clean Fenced Fixture

This fixture exercises the fence-state scanner. It must produce zero
findings from check_markdown.py: no pipe tables, no tabs outside a fence,
no list marker switches, and no unresolved reference links. The three
fenced blocks below carry the constructs that trip a naive line scanner:
a shebang, a C include, and a tab-indented Makefile rule.

## Shell snippet

```bash
#!/usr/bin/env bash
set -euo pipefail
echo "hello"
```

## C snippet

```c
#include <stdio.h>

int main(void) {
    printf("hello\n");
    return 0;
}
```

## Makefile snippet

```makefile
build:
	go build ./...

test:
	go test ./...
```

## Tilde fence with a backtick in its info string

A backtick in a tilde fence's info string is allowed, unlike a backtick
fence's info string.

~~~text with a ` backtick
This line is ordinary content inside the tilde fence.
~~~

## Ordinary prose

A short paragraph with a resolved reference link to the [style guide][style].

- one
- two
- three

1. first
2. second
3. third

[style]: https://example.com/style-guide "Style Guide"
