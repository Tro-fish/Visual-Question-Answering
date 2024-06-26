import torch
import torch.nn as nn
import torchvision.transforms as transforms
from PIL import Image
from transformers import AutoTokenizer
from vqa_model import VQAModel
from parser import test_parser_args

def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])
    image = Image.open(image_path).convert('RGB')
    image = transform(image).unsqueeze(0)  # Add batch dimension
    return image

def preprocess_text(annotation_text, tokenizer):
    tokens = tokenizer.encode_plus(
        annotation_text,
        truncation=True,
        add_special_tokens=True,
        max_length=32,
        padding='max_length',
        return_attention_mask=True,
        return_tensors='pt',
    )
    return tokens

def extract_between_special_tokens(pred, tokenizer):
    # Get the token ids for special tokens
    start_token_id = tokenizer.convert_tokens_to_ids('<s>')
    end_token_id = tokenizer.convert_tokens_to_ids('</s>')
    pad_token_id = tokenizer.convert_tokens_to_ids('<pad>')
    
    # Convert pred to list and remove <pad> tokens
    pred_list = pred.squeeze().tolist()
    filtered_tokens = [token for token in pred_list if token != pad_token_id]
    
    # Extract tokens between <s> and </s>
    if start_token_id in filtered_tokens and end_token_id in filtered_tokens:
        start_index = filtered_tokens.index(start_token_id) + 1
        end_index = filtered_tokens.index(end_token_id)
        filtered_tokens = filtered_tokens[start_index:end_index]
    
    return tokenizer.decode(filtered_tokens)

def main():

    args = test_parser_args()
    # Device Settings
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    
    # Setting up the tokenizer and vocab size
    tokenizer = AutoTokenizer.from_pretrained('roberta-base')
    vocab_size = len(tokenizer)
    
    # Load model
    model = VQAModel.from_pretrained(vqa_model_path, vocab_size, device)
    
    # Image preprocess
    image = preprocess_image(args.image_path).to(device)
    
    # Text preprocess
    tokens = preprocess_text(args.annotation_text, tokenizer)
    tokens = {key: val.to(device) for key, val in tokens.items()}
    
    model.eval()
    # Prediction
    with torch.no_grad():
        outputs = model(image, tokens)
        _, pred = torch.max(outputs, dim=2)
    
    # Extract and decode the predicted answer
    result = extract_between_special_tokens(pred, tokenizer)
    print("Predicted Answer:", result)

if __name__ == "__main__":
    main()