```markdown
# Sentiment Analysis API

This API provides sentiment analysis for Marathi tweets. It takes a tweet as input and returns the original tweet, a cleaned version of the tweet, and predicted probabilities for Negative, Neutral, and Positive sentiments.

## Endpoint

**POST**: `https://sohel1807--sentiment-analysis.modal.run`

### Request

- **Content-Type**: `application/json`
- **Body**:
  ```json
  {
     "tweet":"मी खूप आनंदी आहे . "
 }
  ```

### Response

- **Content-Type**: `application/json`
- **Body**:
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
  ```

## Example Usage

Send a POST request with the tweet in JSON format to get the sentiment analysis.
