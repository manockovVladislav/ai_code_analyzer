import asyncio
import os

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
except ImportError:
    torch = None
    AutoModelForCausalLM = None
    AutoTokenizer = None
    BitsAndBytesConfig = None

from analysis_api_base import AnalysisAPIBase


class LocalModelAPI(AnalysisAPIBase):
    def __init__(self, model_path: str | None = None):
        """Инициализирует локальную модель из папки с весами."""
        if (
            AutoTokenizer is None
            or AutoModelForCausalLM is None
            or BitsAndBytesConfig is None
            or torch is None
        ):
            raise RuntimeError(
                "Не найдены зависимости для локальной модели. Установите torch, transformers и bitsandbytes."
            )

        def pick_device() -> str:
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA недоступна. Требуется видеокарта для локальной модели.")
            return "cuda"

        resolved_path = model_path or os.getenv(
            "LOCAL_MODEL_PATH", "/home/vladislav/models/Phi-3.5-mini-instruct"
        )
        if not os.path.isdir(resolved_path):
            raise RuntimeError(f"Путь к локальной модели не найден: {resolved_path}")
        super().__init__(model_name=os.path.basename(resolved_path))
        self.model_path = resolved_path
        self.max_new_tokens = int(os.getenv("LOCAL_MAX_NEW_TOKENS", "512"))
        self.temperature = float(os.getenv("LOCAL_TEMPERATURE", "0.2"))
        device = pick_device()
        self.device = torch.device(device)
        print(f"LocalModelAPI device: {self.device}")
        dtype = torch.float16
        device_map = {"": "cuda:0"}
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=dtype,
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=dtype,
            device_map=device_map,
            quantization_config=bnb_config,
            trust_remote_code=True,
            attn_implementation="eager",
        )
        self.model.to(self.device)
        self.model.eval()
        print("first param device:", next(self.model.parameters()).device)
        print("cuda mem (GB):", torch.cuda.memory_allocated() / 1024**3)

    def _build_prompt(self, messages: list[dict]) -> str:
        """Формирует промпт в формате chat-template или в fallback-формате."""
        if hasattr(self.tokenizer, "apply_chat_template"):
            try:
                return self.tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            except Exception:
                pass
        parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            parts.append(f"[{role}]\n{content}")
        return "\n\n".join(parts) + "\n\n[assistant]\n"

    def _generate(self, messages: list[dict]) -> str:
        prompt = self._build_prompt(messages)
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        gen_kwargs = {"max_new_tokens": self.max_new_tokens}
        if self.temperature > 0:
            gen_kwargs.update({"do_sample": True, "temperature": self.temperature})
        else:
            gen_kwargs.update({"do_sample": False})
        output_ids = self.model.generate(**inputs, **gen_kwargs)
        new_tokens = output_ids[0][inputs["input_ids"].shape[-1] :]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    async def call_model(self, messages: list[dict]) -> str:
        """Отправляет сообщения в локальную модель и возвращает ответ."""
        try:
            return await asyncio.to_thread(self._generate, messages)
        except Exception as e:
            return f"ERROR: Ошибка локальной модели - {e}"
