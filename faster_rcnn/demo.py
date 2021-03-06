import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
import os, sys, cv2
import argparse
import os.path as osp
import glob
import pandas as pd
np.set_printoptions(precision=3)
this_dir = osp.dirname(__file__)
print(this_dir)
from tensorflow.core.protobuf import saver_pb2
from lib.networks.factory import get_network
from lib.fast_rcnn.config import cfg
from lib.fast_rcnn.test import im_detect
from lib.fast_rcnn.nms_wrapper import nms
from lib.utils.timer import Timer

CLASSES =('__background__', 'Pedestrian', 'Car', 'Cyclist')


# CLASSES = ('__background__','person','bike','motorbike','car','bus')

def vis_detections(im, class_name, dets, fig,ax, image_name,arr,thresh=0.5):
    """Draw detected bounding boxes."""
    inds = np.where(dets[:, -1] >= thresh)[0]
    tmplst=image_name.split("/")
    tstimg="/".join(tmplst[:5])+"/Results/"+"/".join(tmplst[7:-1])+"/Images/"+tmplst[-1]
    
    if len(inds) == 0:
        plt.axis('off')
    	plt.tight_layout()
	fig.savefig(tstimg)
        return
    
    for i in inds:
	tmpr=np.append([class_name],dets[i])
	
	arr=np.append(arr,tmpr)
	
        bbox = dets[i, :4]
        score = dets[i, -1]

        ax.add_patch(
            plt.Rectangle((bbox[0], bbox[1]),
                          bbox[2] - bbox[0],
                          bbox[3] - bbox[1], fill=False,
                          edgecolor='red', linewidth=3.5)
        )
        ax.text(bbox[0], bbox[1] - 2,
                '{:s} {:.3f}'.format(class_name, score),
                bbox=dict(facecolor='blue', alpha=0.5),
                fontsize=14, color='white')

    ax.set_title(('{} detections with '
                  'p({} | box) >= {:.1f}').format(class_name, class_name,
                                                  thresh),
                 fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.draw()
    fig.savefig(tstimg)
    
    #print arr
    return arr

def demo(sess, net, image_name):
    header=['CLASS','Y1','X1','Y2','X2','SCORE']
    
    """Detect object classes in an image using pre-computed object proposals."""
    
    tmplst=image_name.split("/")
    tstimg="/".join(tmplst[:5])+"/Results/"+"/".join(tmplst[7:-1])+"/CSVs/"+tmplst[-1]
    tstcsv=tstimg[:-3]+"csv"

    pd.DataFrame([]).to_csv(tstcsv)
    # Load the demo image
    im = cv2.imread(image_name)

    # Detect all object classes and regress object bounds
    timer = Timer()
    timer.tic()
    scores, boxes = im_detect(sess, net, im)
    timer.toc()
    #print ('Detection took {:.3f}s for '
    #       '{:d} object proposals').format(timer.total_time, boxes.shape[0])

    # Visualize detections for each class
    im = im[:, :, (2, 1, 0)]

    #cv2.imwrite("/home/dell/Desktop/"+image_name.split("/")[-1],im)
    fig, ax = plt.subplots(figsize=(19.2, 10.8))
    ax.imshow(im, aspect='equal')
    
    CONF_THRESH = 0.8
    NMS_THRESH = 0.3
    tmp=[]
    for cls_ind, cls in enumerate(CLASSES[1:]):
        cls_ind += 1  # because we skipped background
        cls_boxes = boxes[:, 4 * cls_ind:4 * (cls_ind + 1)]
        cls_scores = scores[:, cls_ind]
	
        dets = np.hstack((cls_boxes,
                          cls_scores[:, np.newaxis])).astype(np.float32)
	
        keep = nms(dets, NMS_THRESH)
	
        dets = dets[keep, :]
	
	

        arr=vis_detections(im, cls, dets, fig,ax, image_name,tmp,thresh=CONF_THRESH)
    	if arr is not None:
		tmp=arr
		tmp2=np.reshape(arr,(len(arr)/6,6))
		
		pd.DataFrame(tmp2,columns=header).to_csv(tstcsv,index=False)
#		np.savetxt(, tmp2, delimiter=",")
    
    plt.clf()
    plt.cla()
    plt.close()
    return timer.total_time

def parse_args():
    """Parse input arguments."""
    parser = argparse.ArgumentParser(description='Faster R-CNN demo')
    parser.add_argument('--gpu', dest='gpu_id', help='GPU device id to use [0]',
                        default=0, type=int)
    parser.add_argument('--cpu', dest='cpu_mode',
                        help='Use CPU mode (overrides --gpu)',
                        action='store_true')
    parser.add_argument('--net', dest='demo_net', help='Network to use [vgg16]',
                        default='VGGnet_test')
    parser.add_argument('--model', dest='model', help='Model path',
                        default=' ')

    args = parser.parse_args()

    return args	


if __name__ == '__main__':
    cfg.TEST.HAS_RPN = True  # Use RPN for proposals

    args = parse_args()

    if args.model == ' ' or not os.path.exists(args.model):
        print ('current path is ' + os.path.abspath(__file__))
        raise IOError(('Error: Model not found.\n'))

    # init session
    sess = tf.Session(config=tf.ConfigProto(allow_soft_placement=True))
    # load network
    net = get_network(args.demo_net)
    # load model
    print ('Loading network {:s}... '.format(args.demo_net)),
    saver = tf.train.Saver()
    latest_checkpoint=tf.train.latest_checkpoint(args.model)
    if latest_checkpoint is not None:
	print ("ABCDFGHIJKLLMNOPQRSTUVWXYZ")
	saver.restore(sess,latest_checkpoint)
	print ("ABCDFGHIJKLLMNOPQRSTUVWXYZ")
	print("Model Restores from {}".format(latest_checkpoint))
    #saver.restore(sess, args.model)
    print (' done.')
    #saver =tf.train.Saver(write_version =saver_pb2.SaverDef.V1)
    #ckpt =tf.train.get_checkpoint_state(args.model)
    #print("ckpt:", ckpt)
    #if ckpt and ckpt.model_checkpoint_path:
#	saver.restore(sess,ckpt.model_checkpoint_path)
#        print (' done.')

    # Warmup on a dummy image
    im = 128 * np.ones((300, 300, 3), dtype=np.uint8)
    for i in xrange(2):
        _, _ = im_detect(sess, net, im)

    #im_names = glob.glob(os.path.join(cfg.DATA_DIR, 'demo', '*.png')) + \
     #          glob.glob(os.path.join(cfg.DATA_DIR, 'demo', '*.jpg'))
    pathdir="/combo/BTP/Codes/TFFRCNN/data/Indian/"
#    im_names=os.listdir(pathdir)
#    print im_names
    

    for im_names in [pathdir+"Indian_training/",pathdir+"Indian_testing/"]:
	    bill=os.listdir(im_names)	
	    for imn in bill:
		print im_names.split("/")[-2],imn
		bill2=os.listdir(im_names+imn)
		tme=[]
    		tme2=[]
		cntr=0
		for im_name in bill2:
			temer = Timer()
		    	temer.tic()
			#print '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
			#print 'Demo for {:s}'.format(im_name)
			time=demo(sess, net, im_names+imn+"/"+im_name)
			temer.toc()
			tme2.append(temer.total_time)
			tme.append(time)
		#    print tme
		csvpath="/combo/BTP/Codes/TFFRCNN/Results/"+im_names.split("/")[-2]+"/"+imn+"/"+imn+"_time.csv"
		pd.DataFrame(np.vstack((np.array(bill2),np.array(tme),np.array(tme2))).T,columns=['FILE_NAME','DETECTION_TIME','TOTAL_TIME']).to_csv(csvpath,index=False)
	

    #plt.show()

