from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
import tiktoken

logger = logging.getLogger(__name__)

class TokenManager:	
	def __init__(self):
		self.encoder = tiktoken.get_encoding("cl100k_base")
		self.token_costs = {
			"sonar": {"input": 0.001, "output": 0.002},
			"sonar-pro": {"input": 0.003, "output": 0.006},
			"sonar-deep-research": {"input": 0.005, "output": 0.010},
			"sonar-reasoning": {"input": 0.003, "output": 0.006},
			"sonar-reasoning-pro": {"input": 0.005, "output": 0.010}
		}
		
	def count_tokens(self, text: str) -> int:
		try:
			return len(self.encoder.encode(text))
		except:
			return len(text) // 4

	def estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
		costs = self.token_costs.get(model, {"input": 0.001, "output": 0.002})
		return (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1000

	def optimize_prompt(self, prompt: str, max_tokens: int, preserve_sections: List[str] = None) -> str:
		current_tokens = self.count_tokens(prompt)
		if current_tokens <= max_tokens:
			return prompt
		
		preserve_sections = preserve_sections or []
		preserved_content = ""
		for section in preserve_sections:
			if section in prompt:
				start = prompt.find(section)
				end = prompt.find("\n\n", start)
				if end == -1:
					end = len(prompt)
				preserved_content += prompt[start:end] + "\n\n"
		
		preserved_tokens = self.count_tokens(preserved_content)
		remaining_tokens = max_tokens - preserved_tokens - 100
		
		if remaining_tokens <= 0:
			return preserved_content

		other_content = prompt
		for section in preserve_sections:
			other_content = other_content.replace(section, "")
		truncated_content = self._intelligent_truncate(other_content, remaining_tokens)
		return preserved_content + truncated_content

	def _intelligent_truncate(self, text: str, max_tokens: int) -> str:
		"""Intelligently truncate text preserving most important parts"""
		sentences = text.split('. ')

		scored_sentences = []
		for sentence in sentences:
			score = self._score_sentence_importance(sentence)
			tokens = self.count_tokens(sentence)
			scored_sentences.append((sentence, score, tokens))
		
		scored_sentences.sort(key=lambda x: x[1], reverse=True)
		selected_sentences = []
		total_tokens = 0
		for sentence, score, tokens in scored_sentences:
			if total_tokens + tokens <= max_tokens:
				selected_sentences.append(sentence)
				total_tokens += tokens
			else:
				break
		
		return '. '.join(selected_sentences)

	def _score_sentence_importance(self, sentence: str) -> float:
		"""Score sentence importance for truncation decisions"""
		importance_keywords = [
			'research shows', 'study found', 'according to', 'data indicates',
			'expert', 'professor', 'analysis reveals', 'significant', 'important',
			'key finding', 'conclusion', 'result', 'evidence', 'prove'
		]
		
		score = 0.0
		sentence_lower = sentence.lower()
		
		for keyword in importance_keywords:
			if keyword in sentence_lower:
				score += 2.0
		
		# Length penalty (very short or very long sentences are less important)
		length = len(sentence.split())
		if 10 <= length <= 30:
			score += 1.0
		elif length < 5:
			score -= 1.0
		
		# Numbers and statistics are important
		if any(char.isdigit() for char in sentence):
			score += 1.5
		
		# Citations are important
		if any(indicator in sentence for indicator in ['(', '[', 'http']):
			score += 1.0
		
		return score

	def select_optimal_model(self, task_type: str, complexity: float, budget_factor: float = 1.0) -> str:
		"""Select optimal model based on task requirements and budget"""
		
		# Model capabilities vs cost
		model_matrix = {
			"sonar": {"capability": 0.6, "cost": 1.0, "speed": 1.0},
			"sonar-pro": {"capability": 0.8, "cost": 3.0, "speed": 0.8},
			"sonar-deep-research": {"capability": 0.95, "cost": 5.0, "speed": 0.6},
			"sonar-reasoning": {"capability": 0.75, "cost": 3.0, "speed": 0.8},
			"sonar-reasoning-pro": {"capability": 0.9, "cost": 5.0, "speed": 0.6}
		}
		
		# Task type requirements
		task_requirements = {
			"quick_lookup": {"min_capability": 0.5, "speed_weight": 0.8},
			"standard_research": {"min_capability": 0.7, "speed_weight": 0.6},
			"deep_analysis": {"min_capability": 0.8, "speed_weight": 0.3},
			"fact_verification": {"min_capability": 0.85, "speed_weight": 0.4},
			"synthesis": {"min_capability": 0.75, "speed_weight": 0.5}
		}
		
		requirements = task_requirements.get(task_type, task_requirements["standard_research"])
		min_capability = requirements["min_capability"] + (complexity * 0.2)
		speed_weight = requirements["speed_weight"]
		
		best_model = "sonar"
		best_score = 0.0
		for model, specs in model_matrix.items():
			if specs["capability"] < min_capability:
				continue
			# Value score = capability / (cost * budget_factor) + speed * speed_weight
			value_score = (
				specs["capability"] / (specs["cost"] * budget_factor) +
				specs["speed"] * speed_weight
			)
			
			if value_score > best_score:
				best_score = value_score
				best_model = model
		
		return best_model

	def calculate_value_score(self, response_quality: float, input_tokens: int, output_tokens: int, model: str) -> float:
		cost = self.estimate_cost(model, input_tokens, output_tokens)
		if cost == 0:
			return 0.0
		# Value = (Quality^2 * Output_Tokens) / (Cost * 1000)
		value_score = (response_quality ** 2 * output_tokens) / (cost * 1000)
		return value_score