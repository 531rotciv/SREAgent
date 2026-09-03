from transformers import AutoModelForCausalLM, AutoTokenizer
from config_loader import load_config, get_model


# LocalLLM class is responsible for loading a local language model and providing methods to generate 
# text based on input messages. It uses the Hugging Face Transformers library to load the model and tokenizer, 
# supports synchronous text generation.
class LocalLLM:

    def __init__(self):
        model_name = get_model(load_config())
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto",
        )

    # Generates text based on input messages and optional tools. It applies a chat template to the messages,
    # tokenizes them, and then generates text using the model. The generated text is decoded and returned as a string. 
    def generate(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        max_new_tokens: int = 512,
    ) -> str:

        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tools=tools,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
        )

        generated = outputs[0][inputs["input_ids"].shape[-1]:]

        return self.tokenizer.decode(
            generated,
            skip_special_tokens=True,
        )