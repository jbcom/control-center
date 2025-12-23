# Documentation

This directory contains additional documentation for this Rust crate.

## API Documentation

Rust crates are documented using [rustdoc](https://doc.rust-lang.org/rustdoc/). View the generated documentation at:

```
https://docs.rs/${CRATE_NAME}
```

Or generate locally:

```bash
# Generate documentation
cargo doc --no-deps --open

# Generate with private items
cargo doc --no-deps --document-private-items --open

# Build docs for all workspace members
cargo doc --workspace --no-deps
```

## Writing Good Documentation

Follow these conventions for consistent, jbcom-branded documentation:

### Crate-Level Documentation

Add a `//!` comment block at the top of `src/lib.rs`:

```rust
//! # Crate Name
//!
//! Brief description of what this crate does.
//!
//! ## Features
//!
//! - Feature 1
//! - Feature 2
//!
//! ## Quick Start
//!
//! ```rust
//! use crate_name::Client;
//!
//! let client = Client::new();
//! let result = client.process("input")?;
//! ```
//!
//! ## Examples
//!
//! See the [`examples`](https://github.com/jbcom/crate-name/tree/main/examples)
//! directory for complete examples.
```

### Function Documentation

```rust
/// Processes the input and returns the transformed result.
///
/// This function applies the configured transformations to the input
/// string and returns the result. It is safe for concurrent use.
///
/// # Arguments
///
/// * `input` - The string to process
///
/// # Returns
///
/// The processed string, or an error if processing fails.
///
/// # Errors
///
/// Returns [`ProcessError::InvalidInput`] if the input is empty.
/// Returns [`ProcessError::Timeout`] if processing takes too long.
///
/// # Examples
///
/// ```rust
/// use crate_name::process;
///
/// let result = process("hello")?;
/// assert_eq!(result, "HELLO");
/// ```
///
/// # Panics
///
/// Panics if the global configuration is not initialized.
pub fn process(input: &str) -> Result<String, ProcessError> {
    // ...
}
```

### Struct Documentation

```rust
/// A client for interacting with the API.
///
/// The client handles authentication, connection pooling, and
/// request/response serialization. It should be reused across
/// multiple requests.
///
/// # Examples
///
/// ```rust
/// use crate_name::Client;
///
/// let client = Client::builder()
///     .timeout(Duration::from_secs(30))
///     .build()?;
///
/// let response = client.get("/api/users").await?;
/// ```
#[derive(Debug, Clone)]
pub struct Client {
    /// The base URL for API requests.
    pub base_url: String,
    
    /// Request timeout duration.
    timeout: Duration,
}
```

### Module Documentation

Create a `mod.rs` or use `//!` at the top of module files:

```rust
//! HTTP client utilities.
//!
//! This module provides HTTP client functionality including:
//!
//! - Connection pooling via [`Pool`]
//! - Request building via [`RequestBuilder`]
//! - Response parsing via [`Response`]
//!
//! # Examples
//!
//! ```rust
//! use crate_name::http::{Client, Request};
//!
//! let client = Client::new();
//! let request = Request::get("https://api.example.com");
//! let response = client.execute(request).await?;
//! ```
```

## Custom Styling

To apply jbcom branding to locally generated docs, create a custom CSS file:

### docs/jbcom-rustdoc.css

```css
/* jbcom brand colors for rustdoc */
:root {
    --main-background-color: #0a0f1a;
    --main-color: #f1f5f9;
    --settings-input-color: #111827;
    --sidebar-background-color: #111827;
    --headings-border-bottom-color: #1e293b;
    --search-input-focused-border-color: #06b6d4;
    --stab-background-color: #1e293b;
    --code-highlight-kw-color: #c678dd;
    --code-highlight-self-color: #06b6d4;
    --code-highlight-string-color: #98c379;
}
```

### Apply with cargo doc

```bash
# Copy CSS to target directory after build
cargo doc --no-deps
cp docs/jbcom-rustdoc.css target/doc/

# Or use environment variable
RUSTDOCFLAGS="--extend-css docs/jbcom-rustdoc.css" cargo doc --no-deps
```

## Documentation Tests

Rust runs code examples in documentation as tests:

```bash
# Run doc tests
cargo test --doc

# Run all tests including doc tests
cargo test
```

## jbcom Brand Guidelines

See the central [DESIGN-SYSTEM.md](../../always-sync/docs/DESIGN-SYSTEM.md) for:
- Color palette
- Typography standards
- Accessibility requirements

## Additional Resources

- [The rustdoc Book](https://doc.rust-lang.org/rustdoc/)
- [RFC 1574 - API Documentation Conventions](https://rust-lang.github.io/rfcs/1574-more-api-documentation-conventions.html)
- [docs.rs](https://docs.rs/)
