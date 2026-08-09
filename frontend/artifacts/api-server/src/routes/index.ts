import { Router, type IRouter } from "express";
import healthRouter from "./health";
import gawahRouter from "./gawah";

const router: IRouter = Router();

router.use(healthRouter);
router.use(gawahRouter);

export default router;
