// Package ollama provides a Go client for the Ollama Cloud API.
//
// This package enables AI-powered code review, failure analysis, and issue
// triage using Ollama's GLM 4.6 model. It provides both raw chat capabilities
// and structured analysis methods.
//
// # Usage
//
//	client := ollama.New("your-api-key")
//
//	// Simple chat
//	response, err := client.Chat("Explain this code...")
//
//	// With system prompt
//	response, err := client.ChatWithSystem(
//	    "You are a code reviewer.",
//	    "Review this function...",
//	)
//
//	// Structured code review
//	review, err := client.ReviewCode(diff)
//	for _, issue := range review.Issues {
//	    fmt.Printf("%s: %s\n", issue.Severity, issue.Description)
//	}
//
//	// CI failure analysis
//	analysis, err := client.AnalyzeFailure(logs)
//	fmt.Println("Root cause:", analysis.RootCause)
//
// # Model
//
// The default model is "glm-4.6:cloud", which provides:
//   - Fast response times
//   - Code-aware analysis
//   - Structured JSON output
//
// # Authentication
//
// Requires an OLLAMA_API_KEY environment variable or explicit key in New().
package ollama
