"""
LLM-related commands for the chatbot CLI.
Allows users to switch models and providers during runtime.
"""

import os
from typing import Optional, Tuple
from base_utils.llm_factory import LLMFactory, LLMConfig
from base_utils.utils import print_system, print_error, Colors


class LLMCommands:
    """Handle LLM-related commands in the chatbot."""
    
    @staticmethod
    def parse_model_command(command: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse a model switch command.
        
        Args:
            command: The command string (e.g., "/model openai o3")
            
        Returns:
            Tuple of (provider, model) or (None, None) if not a model command
        """
        if not command.startswith("/model"):
            return None, None
        
        parts = command.split()
        if len(parts) == 1:
            # Just "/model" - show current configuration
            return "show", None
        elif len(parts) == 2:
            # "/model <provider>" or "/model <alias>"
            provider_or_alias = parts[1].lower()
            
            # Check if it's a model alias
            if provider_or_alias in LLMConfig.MODEL_ALIASES:
                # It's a model alias, determine provider
                model = LLMConfig.MODEL_ALIASES[provider_or_alias]
                provider = LLMCommands._get_provider_for_model(model)
                return provider, provider_or_alias
            else:
                # It's a provider, use default model
                return provider_or_alias, None
        else:
            # "/model <provider> <model>"
            return parts[1].lower(), parts[2].lower()
    
    @staticmethod
    def _get_provider_for_model(model: str) -> str:
        """Determine the provider for a given model."""
        if "claude" in model:
            return LLMConfig.ANTHROPIC
        elif "gpt" in model or model.startswith("o"):
            return LLMConfig.OPENAI
        elif "gemini" in model:
            return LLMConfig.GOOGLE
        else:
            return LLMConfig.OLLAMA
    
    @staticmethod
    def handle_model_command(command: str) -> bool:
        """
        Handle a model switch command.
        
        Returns:
            bool: True if command was handled, False otherwise
        """
        provider, model = LLMCommands.parse_model_command(command)
        
        if provider is None:
            return False
        
        if provider == "show":
            # Show current configuration
            current_provider = os.getenv("LLM_PROVIDER", "anthropic")
            current_model = os.getenv("LLM_MODEL", "default")
            print_system(f"\nCurrent LLM Configuration:")
            print_system(f"  Provider: {Colors.BLUE}{current_provider}{Colors.ENDC}")
            print_system(f"  Model: {Colors.BLUE}{current_model}{Colors.ENDC}")
            
            # Show available models
            print_system(f"\nAvailable Models:")
            all_models = LLMFactory.get_available_models()
            for prov, models in all_models.items():
                print_system(f"\n  {Colors.YELLOW}{prov}:{Colors.ENDC}")
                for m in models:
                    alias = LLMCommands._get_alias_for_model(m)
                    if alias:
                        print_system(f"    - {m} (alias: {alias})")
                    else:
                        print_system(f"    - {m}")
            
            print_system(f"\nUsage: /model <provider> [model]")
            print_system(f"   or: /model <alias>")
            return True
        
        # Validate provider
        valid_providers = [LLMConfig.ANTHROPIC, LLMConfig.OPENAI, LLMConfig.GOOGLE, 
                          LLMConfig.OLLAMA, LLMConfig.HARVARD, LLMConfig.CUSTOM_OPENAI]
        if provider not in valid_providers:
            print_error(f"Unknown provider: {provider}")
            print_system(f"Available providers: {', '.join(valid_providers)}")
            return True
        
        # Set the new configuration
        os.environ["LLM_PROVIDER"] = provider
        
        if model:
            # Resolve alias if needed
            resolved_model = LLMConfig.MODEL_ALIASES.get(model, model)
            
            # Validate model for provider
            if not LLMFactory.validate_model(provider, model):
                print_error(f"Model '{model}' is not available for provider '{provider}'")
                available = LLMFactory.get_available_models(provider)[provider]
                print_system(f"Available models for {provider}: {', '.join(available)}")
                return True
            
            os.environ["LLM_MODEL"] = resolved_model
            print_system(f"Switched to {Colors.GREEN}{provider}{Colors.ENDC} with model {Colors.GREEN}{model}{Colors.ENDC}")
        else:
            # Use default model for provider
            default_model = LLMConfig.DEFAULT_MODELS.get(provider)
            if default_model:
                os.environ["LLM_MODEL"] = default_model
            print_system(f"Switched to {Colors.GREEN}{provider}{Colors.ENDC} with default model")
        
        print_system("Note: This will take effect for new conversations. Current conversation continues with existing model.")
        return True
    
    @staticmethod
    def _get_alias_for_model(model: str) -> Optional[str]:
        """Get the alias for a model if it exists."""
        for alias, full_model in LLMConfig.MODEL_ALIASES.items():
            if full_model == model:
                return alias
        return None
    
    @staticmethod
    def show_help():
        """Show help for model commands."""
        help_text = f"""
{Colors.BOLD}Model Switching Commands:{Colors.ENDC}

  {Colors.YELLOW}/model{Colors.ENDC}                    - Show current LLM configuration
  {Colors.YELLOW}/model <provider>{Colors.ENDC}         - Switch to provider with default model
  {Colors.YELLOW}/model <provider> <model>{Colors.ENDC} - Switch to specific provider and model
  {Colors.YELLOW}/model <alias>{Colors.ENDC}            - Switch using model alias

{Colors.BOLD}Examples:{Colors.ENDC}
  /model                    - Show current configuration
  /model openai             - Switch to OpenAI with default model
  /model openai o3          - Switch to OpenAI's o3 model
  /model gpt-4              - Switch to GPT-4 (alias)
  /model claude-sonnet-4    - Switch to Claude Sonnet 4 (alias)

{Colors.BOLD}Available Aliases:{Colors.ENDC}
  {Colors.CYAN}Anthropic:{Colors.ENDC} claude-opus, claude-sonnet, claude-haiku, claude-sonnet-4
  {Colors.CYAN}OpenAI:{Colors.ENDC} gpt-4, gpt-4-turbo, gpt-3.5, o1, o1-mini, o3, o3-mini
  {Colors.CYAN}Google:{Colors.ENDC} gemini, gemini-vision
  {Colors.CYAN}Ollama:{Colors.ENDC} llama2, mistral, codellama
  {Colors.CYAN}Harvard:{Colors.ENDC} harvard-o3-mini, harvard-gpt4-mini
"""
        print(help_text)