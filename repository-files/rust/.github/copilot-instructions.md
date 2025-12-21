# Rust Copilot Instructions

## Environment Setup

### Toolchain
```bash
# Install Rust via rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Ensure stable toolchain
rustup default stable

# Add development components
rustup component add clippy rustfmt rust-analyzer
```

### Project Setup
```bash
# Install dependencies
cargo build

# Verify setup
cargo test
```

## Development Commands

### Testing (ALWAYS run tests)
```bash
# Run all tests
cargo test

# Run specific test
cargo test test_name

# Run tests with output
cargo test -- --nocapture

# Run doc tests only
cargo test --doc

# Run ignored tests
cargo test -- --ignored
```

### Linting & Formatting
```bash
# Format code
cargo fmt

# Check formatting (CI mode)
cargo fmt -- --check

# Run clippy linter
cargo clippy

# Fail on warnings (CI mode)
cargo clippy -- -D warnings
```

### Building
```bash
# Debug build
cargo build

# Release build
cargo build --release

# Check without full build
cargo check
```

### Documentation
```bash
# Generate and open docs
cargo doc --no-deps --open

# With private items
cargo doc --no-deps --document-private-items
```

## Code Patterns

### Error Handling
```rust
// Define custom error types
#[derive(Debug, thiserror::Error)]
pub enum ProcessError {
    #[error("invalid input: {0}")]
    InvalidInput(String),
    
    #[error("operation timed out")]
    Timeout,
    
    #[error(transparent)]
    Io(#[from] std::io::Error),
}

// Use Result with ? operator
fn process(input: &str) -> Result<Output, ProcessError> {
    let validated = validate(input)?;
    let transformed = transform(validated)?;
    Ok(Output::new(transformed))
}
```

### Async Patterns
```rust
use tokio;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let result = fetch_data("https://api.example.com").await?;
    println!("{:?}", result);
    Ok(())
}

async fn fetch_data(url: &str) -> Result<Response, reqwest::Error> {
    let client = reqwest::Client::new();
    client.get(url).send().await?.json().await
}
```

### Testing Patterns
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_process_valid_input() {
        let result = process("valid").unwrap();
        assert_eq!(result.value, "expected");
    }

    #[test]
    fn test_process_invalid_input() {
        let result = process("");
        assert!(matches!(result, Err(ProcessError::InvalidInput(_))));
    }

    #[tokio::test]
    async fn test_async_operation() {
        let result = async_operation().await.unwrap();
        assert!(result.success);
    }
}
```

### Builder Pattern
```rust
#[derive(Debug, Default)]
pub struct ClientBuilder {
    timeout: Option<Duration>,
    retries: Option<u32>,
}

impl ClientBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn timeout(mut self, timeout: Duration) -> Self {
        self.timeout = Some(timeout);
        self
    }

    pub fn retries(mut self, retries: u32) -> Self {
        self.retries = Some(retries);
        self
    }

    pub fn build(self) -> Result<Client, BuildError> {
        Ok(Client {
            timeout: self.timeout.unwrap_or(Duration::from_secs(30)),
            retries: self.retries.unwrap_or(3),
        })
    }
}
```

## Common Issues

### Borrow Checker Errors
```rust
// Clone if ownership is needed
let owned = borrowed.clone();

// Use references when possible
fn process(data: &Data) -> Result { ... }

// Use Arc for shared ownership
use std::sync::Arc;
let shared = Arc::new(data);
```

### Lifetime Annotations
```rust
// Explicit lifetimes when needed
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}

// Struct with references
struct Parser<'a> {
    input: &'a str,
}
```

## File Structure
```
src/
├── lib.rs           # Library entry point
├── main.rs          # Binary entry point
├── error.rs         # Error types
├── config.rs        # Configuration
├── client/          # Module directory
│   ├── mod.rs       # Module root
│   └── http.rs      # Submodule
tests/
├── integration.rs   # Integration tests
benches/
├── benchmark.rs     # Benchmarks
```
