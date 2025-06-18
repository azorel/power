#!/usr/bin/env python3
"""
Claude Sonnet 4/Opus 4 Configuration Demo
Showcases the new hybrid reasoning and 64K token capabilities.
"""

import asyncio
import json
from adapters.claude_api.config import ClaudeConfig
from adapters.claude_api.unified_client import ClaudeUnifiedClient
from shared.models.llm_request import LLMRequest


async def demo_claude_sonnet4_capabilities():
    """Demonstrate Claude Sonnet 4/Opus 4 enhanced capabilities."""
    
    print("🤖 Claude Sonnet 4/Opus 4 Configuration Demo")
    print("=" * 50)
    
    # Initialize configuration
    config = ClaudeConfig()
    
    print(f"✓ Default Model: {config.default_model}")
    print(f"✓ Max Tokens: {config.default_max_tokens:,} (64K token context)")
    print(f"✓ Knowledge Cutoff: March 2025")
    print(f"✓ Hybrid Reasoning: {config.enable_hybrid_reasoning}")
    print(f"✓ Reasoning Mode: {config.reasoning_mode}")
    print()
    
    # Display model configurations
    print("📋 Available Models:")
    for model in config.get_supported_models():
        model_config = config.get_model_config(model)
        print(f"  • {model}")
        print(f"    - Max Tokens: {model_config.get('max_tokens', 'N/A'):,}")
        print(f"    - Knowledge Cutoff: {model_config.get('knowledge_cutoff', 'N/A')}")
        print(f"    - Hybrid Reasoning: {model_config.get('supports_hybrid_reasoning', False)}")
        print(f"    - Model Type: {model_config.get('model_type', 'N/A')}")
        print()
    
    # Display hybrid reasoning configuration
    print("🧠 Hybrid Reasoning Configuration:")
    reasoning_config = config.get_hybrid_reasoning_config()
    print(f"  • Enabled: {reasoning_config['enabled']}")
    print(f"  • Mode: {reasoning_config['mode']}")
    print(f"  • Depth: {reasoning_config['depth']}")
    print(f"  • Step-by-step: {reasoning_config['step_by_step']}")
    print("  • Capabilities:")
    for capability, enabled in reasoning_config['capabilities'].items():
        status = "✓" if enabled else "✗"
        print(f"    {status} {capability.replace('_', ' ').title()}")
    print()
    
    # Validate configuration
    print("🔍 Configuration Validation:")
    errors = config.validate()
    if errors:
        print("  ❌ Configuration has errors:")
        for error in errors:
            print(f"    - {error}")
    else:
        print("  ✅ Configuration is valid!")
    print()
    
    # Display enhanced features
    print("🚀 Enhanced Features:")
    features = [
        ("Function Calling", config.enable_function_calling),
        ("Tool Use", config.enable_tool_use),
        ("Vision", config.enable_vision),
        ("Document Analysis", config.enable_document_analysis),
        ("Code Analysis", config.enable_code_analysis),
        ("Streaming", config.enable_streaming),
        ("Response Cache", config.enable_response_cache),
        ("Content Filter", config.enable_content_filter)
    ]
    
    for feature_name, enabled in features:
        status = "✓" if enabled else "✗"
        print(f"  {status} {feature_name}")
    print()
    
    # Display context management
    print("📄 Context Management (64K Tokens):")
    print(f"  • Max Context Tokens: {config.max_context_tokens:,}")
    print(f"  • Window Management: {config.context_window_management}")
    print(f"  • Preservation Ratio: {config.context_preservation_ratio:.0%}")
    print()
    
    # Performance optimization
    print("⚡ Performance Optimization:")
    print(f"  • Rate Limit (per minute): {config.rate_limit_per_minute}")
    print(f"  • Rate Limit (per hour): {config.rate_limit_per_hour}")
    print(f"  • Rate Limit (per day): {config.rate_limit_per_day}")
    print(f"  • Cache TTL: {config.cache_ttl_seconds:,} seconds")
    print(f"  • Max Cache Size: {config.max_cache_size:,} entries")
    print()
    
    # Safety and moderation
    print("🛡️ Safety & Moderation:")
    print(f"  • Safety Level: {config.safety_level}")
    print(f"  • Content Filter: {config.enable_content_filter}")
    print(f"  • Ethical Guidelines: {config.enable_ethical_guidelines}")
    print()
    
    print("🎯 Configuration Summary:")
    config_dict = config.to_dict()
    
    # Display key configuration aspects
    summary_items = [
        "default_model",
        "default_max_tokens",
        "hybrid_reasoning_config",
        "max_context_tokens",
        "supported_models"
    ]
    
    for item in summary_items:
        if item in config_dict:
            if item == "supported_models":
                print(f"  • {item}: {len(config_dict[item])} models")
            elif item == "hybrid_reasoning_config":
                hr_config = config_dict[item]
                print(f"  • {item}: {hr_config['mode']} mode, depth {hr_config['depth']}")
            else:
                print(f"  • {item}: {config_dict[item]}")
    
    print()
    print("✨ Claude Sonnet 4/Opus 4 configuration completed!")
    print("   Ready for enhanced AI capabilities with hybrid reasoning.")
    

def demo_model_comparison():
    """Compare different Claude models."""
    config = ClaudeConfig()
    
    print("📊 Model Comparison:")
    print("-" * 80)
    print(f"{'Model':<25} {'Tokens':<10} {'Hybrid':<8} {'Cost/1K':<12} {'Type':<15}")
    print("-" * 80)
    
    for model in config.get_supported_models():
        model_config = config.get_model_config(model)
        max_tokens = f"{model_config.get('max_tokens', 0):,}"
        hybrid = "Yes" if model_config.get('supports_hybrid_reasoning', False) else "No"
        cost = f"${model_config.get('cost_per_1k_input_tokens', 0):.3f}"
        model_type = model_config.get('model_type', 'N/A')
        
        print(f"{model:<25} {max_tokens:<10} {hybrid:<8} {cost:<12} {model_type:<15}")
    
    print("-" * 80)


if __name__ == "__main__":
    print("🚀 Starting Claude Sonnet 4/Opus 4 Demo...")
    print()
    
    # Run the main demo
    asyncio.run(demo_claude_sonnet4_capabilities())
    
    print()
    demo_model_comparison()
    
    print()
    print("🎉 Demo completed! Claude Sonnet 4/Opus 4 is ready for use.")