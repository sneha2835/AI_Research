import os
import shutil

# Path to the folder containing all topic subfolders
base_dir = r"D:\Research\backend\datasets\research-papers\papers"

# List of folders to KEEP (AI, ML, DL, Data Science relevant)
folders_to_keep = {
    "adversarial-attack",
    "adversarial-defense",
    "adversarial-robustness",
    "atari-games",
    "audio-classification",
    "automatic-speech-recognition",
    "benchmarking",
    "causal-discovery",
    "causal-inference",
    "classification",
    "classification-1",
    "code-generation",
    "common-sense-reasoning",
    "community-question-answering",
    "computational-efficiency",
    "continuous-control",
    "contrastive-learning",
    "decision-making",
    "decoder",
    "denoising",
    "dialogue-generation",
    "diversity",
    "graph-learning",
    "graph-neural-network",
    "image-classification",
    "knowledge-graphs",
    "language-identification",
    "language-modelling",
    "link-prediction",
    "logical-reasoning",
    "machine-learning",
    "medical-image-analysis",
    "medical-image-segmentation",
    "motion-planning",
    "music-generation",
    "music-information-retrieval",
    "music-source-separation",
    "music-transcription",
    "nmt",
    "node-classification",
    "object",
    "object-detection",
    "offline-rl",
    "openai-gym",
    "open-domain-question-answering",
    "question-answering",
    "recommendation-systems",
    "reinforcement-learning",
    "reinforcement-learning-1",
    "representation-learning",
    "retrieval",
    "robot-navigation",
    "semantic-segmentation",
    "sentence",
    "speech-enhancement",
    "speech-recognition",
    "speech-synthesis",
    "text-to-image-generation",
    "text-to-sql",
    "time-series",
    "time-series-forecasting",
    "transfer-learning",
    "translation",
    "visual-navigation",
    "visual-odometry",
    "visual-reasoning",
    "voice-conversion",
    "xai",
}

deleted_folders = []

for folder_name in os.listdir(base_dir):
    folder_path = os.path.join(base_dir, folder_name)
    if os.path.isdir(folder_path):
        if folder_name not in folders_to_keep:
            print(f"Deleting folder: {folder_name}")
            shutil.rmtree(folder_path)  # WARNING: deletes folder and all contents
            deleted_folders.append(folder_name)

print(f"\nTotal folders deleted: {len(deleted_folders)}")
print("Deleted folders:", deleted_folders)
