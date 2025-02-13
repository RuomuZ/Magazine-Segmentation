import sys
from argparse import ArgumentParser

from pathlib import Path
import pytorch_lightning as pl
import wandb
from pytorch_lightning.loggers import WandbLogger
from pytorch_lightning.callbacks import (
    LearningRateMonitor,
    ModelCheckpoint,
    RichModelSummary,
    RichProgressBar,
)
sys.path.append(".")
from src.dataset.datamodule import MGZDataModule
from models.model_module import MGZSegmentation
from src.utilities import ESDConfig, PROJ_NAME
ROOT = Path.cwd()


def train(options: ESDConfig):
    wandb.init(project=PROJ_NAME, config=vars(options))
    wandb_logger = WandbLogger(project=PROJ_NAME)
    datamodule = MGZDataModule(processed_dir=options.processed_dir, 
                               raw_dir=options.raw_dir, 
                               batch_size=options.batch_size,
                               seed=options.seed,
                               slice_size=options.slice_size,
                               num_workers=options.num_workers
                               )

    datamodule.prepare_data()
    model_params = vars(options)
    ESDSeg = MGZSegmentation(options.model_type, options.in_channels, options.out_channels, options.learning_rate, model_params)
    callbacks = [
        ModelCheckpoint(
            dirpath=ROOT / "models" / options.model_type,
            filename="{epoch}-{val_loss:.2f}-{other_metric:.2f}",
            save_top_k=0,
            save_last=True,
            verbose=True,
            monitor="val_loss",
            mode="min",
            every_n_train_steps=1000,
        ),
        LearningRateMonitor(),
        RichProgressBar(),
        RichModelSummary(max_depth=3),
    ]
    
    trainer = pl.Trainer(accelerator=options.accelerator, devices=options.devices,
                          num_nodes=1, max_epochs=options.max_epochs,
                          callbacks=callbacks, logger=wandb_logger)
    trainer.fit(model = ESDSeg, datamodule=datamodule)

if __name__ == "__main__":
    # load dataclass arguments from yml file

    config = ESDConfig()
    parser = ArgumentParser()

    parser.add_argument(
        "--model_type",
        type=str,
        help="The model to initialize.",
        default=config.model_type,
    )
    parser.add_argument(
        "--learning_rate",
        type=float,
        help="The learning rate for training model",
        default=config.learning_rate,
    )
    parser.add_argument(
        "--max_epochs",
        type=int,
        help="Number of epochs to train for.",
        default=config.max_epochs,
    )
    parser.add_argument(
        "--raw_dir", type=str, default=config.raw_dir, help="Path to raw directory"
    )
    parser.add_argument(
        "-p", "--processed_dir", type=str, default=config.processed_dir, help="."
    )

    parser.add_argument(
        "--in_channels",
        type=int,
        default=config.in_channels,
        help="Number of input channels",
    )
    parser.add_argument(
        "--out_channels",
        type=int,
        default=config.out_channels,
        help="Number of output channels",
    )
    parser.add_argument(
        "--depth",
        type=int,
        help="Depth of the encoders (CNN only)",
        default=config.depth,
    )
    parser.add_argument(
        "--n_encoders",
        type=int,
        help="Number of encoders (Unet only)",
        default=config.n_encoders,
    )
    parser.add_argument(
        "--embedding_size",
        type=int,
        help="Embedding size of the neural network (CNN/Unet)",
        default=config.embedding_size,
    )
    parser.add_argument(
        "--pool_sizes",
        help="A comma separated list of pool_sizes (CNN only)",
        type=str,
        default=config.pool_sizes,
    )
    parser.add_argument(
        "--kernel_size",
        help="Kernel size of the convolutions",
        type=int,
        default=config.kernel_size,
    )

    parse_args = parser.parse_args()

    config = ESDConfig(**parse_args.__dict__)
    train(config)
