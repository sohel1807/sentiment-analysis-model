# Sentiment Analysis For Marathi Language API

This API analyzes the sentiment of Marathi tweets.  

### **Endpoint**:  
`https://sohel1807--sentiment-analysis.modal.run`  

### **Method**:  
POST  

### **Input**:  
```json
{
 "tweet":"मी खूप आनंदी आहे . "
 }
```  

### **Output**:  
```json
{
  "original_tweet": "मी खूप आनंदी आहे . ",
  "cleaned_tweet": "म खप आनद आह  ",
  "predicted_probabilities": {
    "Negative": 0.013298166657605524,
    "Neutral": 0.011075190415409162,
    "Positive": 0.9756266429269854
  }
}
