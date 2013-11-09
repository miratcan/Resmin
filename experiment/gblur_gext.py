import pygame
import pgext
import sys

img = pygame.image.load('test.jpg')
pgext.filters.blur(img, float(sys.argv[1]))
pygame.image.save(img, "glur_gext_output.jpg")
