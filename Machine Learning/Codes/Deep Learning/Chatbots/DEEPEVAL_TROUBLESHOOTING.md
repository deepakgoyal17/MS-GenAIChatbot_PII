# 🔧 DeepEval Relevance Score Troubleshooting Guide

## 🚨 Problem: Relevance Score Always Shows 0

If your DeepEval relevance scores are consistently showing 0.0, here are the most common causes and solutions:

## 🔍 Diagnostic Steps

### Step 1: Run the Debug Script
```bash
cd "Codes/Deep Learning/Chatbots"
python test_deepeval.py
```

This will help identify the exact issue.

### Step 2: Check the Logs
Look at the Streamlit app logs and `logs/chatbot_app.log` for error messages.

## 🛠️ Common Issues & Solutions

### Issue 1: API Key Problems

**Symptoms:**
- Error messages about authentication
- "GOOGLE_API_KEY not found" warnings

**Solutions:**
1. **Check .env file exists:**
   ```bash
   ls -la .env
   ```

2. **Verify .env file content:**
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

3. **Test API key manually:**
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print(os.getenv("GOOGLE_API_KEY"))  # Should not be None
   ```

### Issue 2: DeepEval Version Compatibility

**Symptoms:**
- Import errors
- Method not found errors
- Unexpected behavior

**Solutions:**
1. **Update DeepEval:**
   ```bash
   pip install --upgrade deepeval
   ```

2. **Check version compatibility:**
   ```bash
   pip show deepeval
   ```

3. **If issues persist, try specific version:**
   ```bash
   pip install deepeval==0.21.73
   ```

### Issue 3: CustomLLM Implementation Issues

**Symptoms:**
- "TypeError: Unsupported type for model" errors
- Model initialization failures

**Solutions:**
1. **Verify inheritance:** Make sure `CustomLLM` inherits from `DeepEvalBaseLLM`
2. **Check required methods:** Ensure all required methods are implemented
3. **Test model generation:** Verify the model can generate responses

### Issue 4: Network/Timeout Issues

**Symptoms:**
- Long delays before returning 0
- Timeout errors in logs

**Solutions:**
1. **Increase timeout in DeepEval:**
   ```python
   relevancy_metric = AnswerRelevancyMetric(
       model=custom_llm,
       threshold=0.5,
       include_reason=True
   )
   ```

2. **Check internet connection**
3. **Try with simpler test cases first**

### Issue 5: Input Format Issues

**Symptoms:**
- Scores work sometimes but not others
- Inconsistent results

**Solutions:**
1. **Ensure inputs are strings:**
   ```python
   question = str(user_prompt).strip()
   answer = str(response.text).strip()
   ```

2. **Check for empty inputs:**
   ```python
   if not question or not answer:
       logger.warning("Empty question or answer")
       return 0.0
   ```

3. **Validate input length:**
   ```python
   if len(question) < 5 or len(answer) < 5:
       logger.warning("Question or answer too short")
   ```

## 🔧 Enhanced Debugging Implementation

Here's an improved version of the DeepEval measurement with better debugging:

```python
def measure_relevancy_with_debug(custom_llm, question, answer, context=""):
    """Enhanced relevancy measurement with comprehensive debugging"""
    
    try:
        # Input validation
        if not question or not answer:
            logger.error("Empty question or answer provided")
            return 0.0
        
        question = str(question).strip()
        answer = str(answer).strip()
        
        logger.info(f"Measuring relevancy for:")
        logger.info(f"  Question ({len(question)} chars): {question[:100]}...")
        logger.info(f"  Answer ({len(answer)} chars): {answer[:100]}...")
        
        # Test model generation first
        test_prompt = "Say 'Hello' if you can generate text."
        test_response = custom_llm.generate(test_prompt)
        logger.info(f"Model test response: {test_response}")
        
        # Create metric with explicit parameters
        relevancy_metric = AnswerRelevancyMetric(
            model=custom_llm,
            threshold=0.5,
            include_reason=True,
            async_mode=False
        )
        
        # Measure with timeout handling
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("DeepEval measurement timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)  # 60 second timeout
        
        try:
            relevancy_metric.measure(question, answer)
            score = relevancy_metric.score
            
            logger.info(f"DeepEval measurement completed:")
            logger.info(f"  Score: {score}")
            
            if hasattr(relevancy_metric, 'reason'):
                logger.info(f"  Reason: {relevancy_metric.reason}")
            
            if hasattr(relevancy_metric, 'success'):
                logger.info(f"  Success: {relevancy_metric.success}")
            
            return score
            
        finally:
            signal.alarm(0)  # Cancel timeout
        
    except TimeoutError:
        logger.error("DeepEval measurement timed out after 60 seconds")
        return 0.0
    except Exception as e:
        logger.error(f"DeepEval measurement failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return 0.0
```

## 🧪 Testing Different Scenarios

### Test Case 1: Simple Question-Answer
```python
question = "What is 2+2?"
answer = "2+2 equals 4."
# Expected: High relevance score (>0.7)
```

### Test Case 2: Partially Relevant
```python
question = "How do I bake a cake?"
answer = "Baking requires an oven and ingredients like flour."
# Expected: Medium relevance score (0.4-0.7)
```

### Test Case 3: Irrelevant
```python
question = "What's the weather today?"
answer = "I like pizza."
# Expected: Low relevance score (<0.3)
```

## 🔄 Alternative Solutions

If DeepEval continues to have issues, consider these alternatives:

### Option 1: Use OpenAI for Evaluation
```python
import openai

def evaluate_with_openai(question, answer):
    prompt = f"""
    Rate the relevance of this answer to the question on a scale of 0.0 to 1.0:
    
    Question: {question}
    Answer: {answer}
    
    Provide only a number between 0.0 and 1.0:
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        score = float(response.choices[0].message.content.strip())
        return max(0.0, min(1.0, score))
    except:
        return 0.0
```

### Option 2: Simple Keyword-Based Relevance
```python
def simple_relevance_score(question, answer):
    """Simple keyword-based relevance scoring"""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([question, answer])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return float(similarity[0][0])
```

## 📞 Getting Help

If none of these solutions work:

1. **Check DeepEval Documentation:** https://docs.confident-ai.com/
2. **GitHub Issues:** https://github.com/confident-ai/deepeval/issues
3. **Enable verbose logging** in your application
4. **Test with minimal example** to isolate the issue

## 🎯 Expected Behavior

When working correctly, you should see:
- Relevance scores between 0.0 and 1.0
- Higher scores for more relevant answers
- Detailed logging of the evaluation process
- Consistent results for the same inputs

Remember: A score of 0.0 usually indicates an error in the evaluation process, not that the answer is completely irrelevant.