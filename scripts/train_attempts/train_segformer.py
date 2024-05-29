import sys
sys.path.append(".")
import torch
from torch.utils.data import DataLoader
import torch.optim as optim
import torch.nn as nn
from pathlib import Path
from src.dataset.datamodule import MGZDataModule
from models.segformer import SegFormerModel  # Importing your SegFormer model
import torch.nn.functional as F

# Setup data paths and datamodule
ROOT = Path.cwd()
processed_dir = ROOT / "data" / "processed"
raw_dir = ROOT / "data" / "raw"
datamodule = MGZDataModule(processed_dir, raw_dir, batch_size=1, slice_size=(4, 4))  # Adjust slice_size if needed
datamodule.prepare_data()
datamodule.setup("fit")

# Create DataLoader
train_loader = DataLoader(datamodule.train_dataset, batch_size=1, shuffle=True)

# Initialize Model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SegFormerModel(input_channels=3, num_classes=3).to(device)

# Loss and Optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training Loop
num_epochs = 5
for epoch in range(num_epochs):
    model.train()
    epoch_loss = 0
    for images, masks in train_loader:
        images = images.to(device)
        masks = masks.to(device)

        masks = masks.long()

        # Forward pass
        outputs = model(images)

        # Debugging shapes
        # print("Output shape before interpolation:", outputs.shape)
        # print("Mask shape expected:", masks.shape)

        # Interpolating to match mask size
        outputs = F.interpolate(outputs, size=(masks.shape[1], masks.shape[2]), mode='bilinear', align_corners=False)

        # Compute loss
        loss = criterion(outputs, masks)  # No squeeze needed since masks are already [batch_size, height, width]

        # Backward and optimize
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        epoch_loss += loss.item()

    print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {epoch_loss / len(train_loader)}")

torch.save(model.state_dict(), "segformer_model.pth")