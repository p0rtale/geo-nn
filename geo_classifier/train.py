import json
import logging
import yaml
import torch
import torchvision

from argparse import Namespace, ArgumentParser
from datetime import datetime
from pathlib import Path

import pytorch_lightning as pl
from torchmetrics.classification import MulticlassAccuracy

from geo_classifier.dataset import PhotoCoordsDataset


class GeoClassifier(pl.LightningModule):
    def __init__(self, hparams: Namespace, freeze=True):
        super().__init__()

        self.save_hyperparameters(hparams)

        self.model = self.__build_model(freeze)

        self.loss_fn = torch.nn.CrossEntropyLoss()
        self.train_acc = MulticlassAccuracy(num_classes=self.hparams.num_classes)
        self.val_acc = MulticlassAccuracy(num_classes=self.hparams.num_classes)

    def __build_model(self, freeze):
        logging.info("Build model")

        model = torchvision.models.resnet50(weights='ResNet50_Weights.DEFAULT')

        if freeze:
            for param in model.parameters():
                param.requires_grad = False

        model.fc = torch.nn.Linear(model.fc.in_features, self.hparams.num_classes)

        return model

    def forward(self, x):
        return self.model(x)

    def configure_optimizers(self):
        optim_feature_extrator = torch.optim.SGD(
            self.parameters(), **self.hparams.optim["params"]
        )

        return {
            "optimizer": optim_feature_extrator,
            "lr_scheduler": {
                "scheduler": torch.optim.lr_scheduler.MultiStepLR(
                    optim_feature_extrator, **self.hparams.scheduler["params"]
                ),
                "interval": "epoch",
                "name": "lr",
            },
        }

    def training_step(self, batch, batch_idx, optimizer_idx=None):
        images, targets, true_lats, true_lngs = batch

        preds = self.model(images)

        loss = self.loss_fn(preds, targets)
        self.train_acc(torch.argmax(preds, dim=1), targets)

        self.log("train_loss", loss, on_step=True, on_epoch=True, prog_bar=True, logger=True)
        self.log("train_acc", self.train_acc, on_step=True, on_epoch=True, prog_bar=True, logger=True)

        return loss

    def validation_step(self, batch, batch_idx):
        images, targets, true_lats, true_lngs = batch

        preds = self.model(images)

        loss = self.loss_fn(preds, targets)
        self.val_acc(torch.argmax(preds, dim=1), targets)

        self.log("val_loss", loss, on_step=True, on_epoch=True, prog_bar=True, logger=True)
        self.log("val_acc", self.val_acc, on_step=True, on_epoch=True, prog_bar=True, logger=True)

    def train_dataloader(self):
        transforms = torchvision.transforms.Compose(
            [
                torchvision.transforms.RandomHorizontalFlip(),
                torchvision.transforms.ToTensor(),
                torchvision.transforms.Normalize(
                    (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
                ),
            ]
        )

        dataset = PhotoCoordsDataset(
            dataset_path=self.hparams.dataset_path,
            images_dir=self.hparams.images_dir,
            transforms=transforms,
        )

        dataloader = torch.utils.data.DataLoader(
            dataset,
            shuffle=True,
            batch_size=self.hparams.batch_size,
            num_workers=self.hparams.num_workers_per_loader,
            pin_memory=True,
        )

        return dataloader

    def val_dataloader(self):
        transforms = torchvision.transforms.Compose(
            [
                torchvision.transforms.Resize(256),
                torchvision.transforms.ToTensor(),
                torchvision.transforms.Normalize(
                    (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
                ),
            ]
        )

        dataset = PhotoCoordsDataset(
            dataset_path=self.hparams.dataset_path,
            images_dir=self.hparams.images_dir,
            transforms=transforms,
        )

        dataloader = torch.utils.data.DataLoader(
            dataset,
            batch_size=self.hparams.batch_size,
            num_workers=self.hparams.num_workers_per_loader,
            pin_memory=True,
        )

        return dataloader


def main(config):
    model_params = config["model_params"]
    trainer_params = config["trainer_params"]

    out_dir = Path(config["out_dir"]) / datetime.now().strftime("%y%m%d-%H%M")
    out_dir.mkdir(exist_ok=True, parents=True)
    logging.info(f"Output directory: {out_dir}")

    logger = pl.loggers.TensorBoardLogger(save_dir=str(out_dir), name="tb_logs")
    checkpoint_dir = out_dir / "ckpts" / "{epoch:03d}-{val_loss:.4f}"
    checkpointer = pl.callbacks.model_checkpoint.ModelCheckpoint(checkpoint_dir)

    trainer = pl.Trainer(
        **trainer_params,
        logger=logger,
        val_check_interval=model_params["val_check_interval"],
        callbacks=[checkpointer],
    )

    model = GeoClassifier(hparams=Namespace(**model_params))
    trainer.fit(model)


def parse_args():
    parser = ArgumentParser()
    parser.add_argument("-c", "--config", type=Path, default=Path("config/model_cells.yml"))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(level=logging.INFO)

    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    main(config)
